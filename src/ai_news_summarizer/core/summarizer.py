"""Summarization logic."""

import inspect
import re

from ai_news_summarizer.llm.base import LLMClient
from ai_news_summarizer.models.schemas import NewsItem, Summary, SummaryConfig


class Summarizer:
    """Generate summaries from news items with an LLM client."""

    def __init__(self, llm_client: LLMClient, config: SummaryConfig):
        self.llm = llm_client
        self.config = config

    def _build_prompt(self, news_item: NewsItem) -> str:
        """Build a deterministic prompt from config and content."""
        style_instruction = {
            "concise": "Keep the summary concise and focused on the main points.",
            "informative": "Cover the key facts and context in an informative way.",
            "detailed": "Provide a more detailed summary with meaningful context.",
        }.get(self.config.style, "Keep the summary concise and focused on the main points.")

        language_instruction = {
            "zh": "Respond in Simplified Chinese.",
            "en": "Respond in English.",
        }.get(self.config.language, "Respond in Simplified Chinese.")

        title_part = f"Title: {news_item.title}\n\n" if self.config.include_title else ""
        content = news_item.content[:2000]

        return (
            "You are a news summarization assistant.\n"
            f"{language_instruction}\n"
            f"{style_instruction}\n"
            f"Use no more than {self.config.max_length} sentences.\n\n"
            f"{title_part}"
            f"Content:\n{content}\n\n"
            "Return only the final summary."
        )

    def _clean_summary(self, text: str) -> str:
        """Remove hidden reasoning tags if a model emits them."""
        parts = text.split("</think>")
        if len(parts) > 1:
            content = parts[-1].strip()
            if content:
                return content
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"<think>.*", "", text)
        return text.strip()

    async def summarize(self, news_item: NewsItem) -> Summary:
        """Generate one summary."""
        if news_item.metadata.get("pre_summarized"):
            score = news_item.metadata.get("score")
            score_prefix = f"[score: {score:g}] " if isinstance(score, (int, float)) else ""
            content = news_item.content.strip() or news_item.title
            return Summary(
                original_url=news_item.url,
                summary=f"{score_prefix}{content}".strip(),
                model=f"source:{news_item.source}",
                token_usage=0,
                metadata={"score": score, "pre_summarized": True},
            )

        prompt = self._build_prompt(news_item)
        summary_text, token_usage = await self.llm.generate_with_usage(prompt)
        summary_text = self._clean_summary(summary_text)

        return Summary(
            original_url=news_item.url,
            summary=summary_text.strip(),
            model=self.llm.model_name,
            token_usage=token_usage,
            metadata={"score": news_item.metadata.get("score")},
        )

    async def summarize_batch(
        self,
        news_items: list[NewsItem],
        max_concurrency: int = 3,
        max_retries: int = 3,
    ) -> list[Summary]:
        """Generate summaries with bounded concurrency and rate-limit retries."""
        import asyncio

        sem = asyncio.Semaphore(max_concurrency)

        async def summarize_with_retry(item: NewsItem) -> Summary:
            for attempt in range(max_retries):
                try:
                    return await self.summarize(item)
                except Exception as exc:
                    error_msg = str(exc).lower()
                    is_rate_limit = (
                        "429" in error_msg
                        or "rate limit" in error_msg
                        or "too many requests" in error_msg
                    )
                    if attempt < max_retries - 1 and is_rate_limit:
                        wait = (2**attempt) * 1.5
                        await asyncio.sleep(wait)
                        continue
                    raise

            return Summary(
                original_url=item.url,
                summary="[summary generation failed, please retry later]",
                model=self.llm.model_name,
                token_usage=0,
            )

        async def bounded_summarize(item: NewsItem) -> Summary:
            async with sem:
                return await summarize_with_retry(item)

        tasks = [bounded_summarize(item) for item in news_items]
        return await asyncio.gather(*tasks)

    async def close(self) -> None:
        """Close the underlying LLM client when supported."""
        close_method = getattr(self.llm, "close", None)
        if close_method is None:
            return

        result = close_method()
        if inspect.isawaitable(result):
            await result
