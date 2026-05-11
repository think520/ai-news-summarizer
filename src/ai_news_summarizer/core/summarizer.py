"""Summarization logic."""

import json
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
            "concise": "摘要要简洁，直接提炼重点。",
            "informative": "摘要要信息充分，覆盖关键事实和背景。",
            "detailed": "摘要要更完整，适合深入了解。",
        }.get(self.config.style, "摘要要简洁，直接提炼重点。")

        language_instruction = {
            "zh": "请使用简体中文。",
            "en": "Respond in English.",
        }.get(self.config.language, "请使用简体中文。")

        title_part = f"标题：{news_item.title}\n\n" if self.config.include_title else ""
        content = news_item.content[:2000]

        return (
            "你是一个新闻情报筛选助手。\n"
            f"{language_instruction}\n"
            f"{style_instruction}\n"
            f"请给这条内容打一个 0-10 的推荐分，分数越高代表越值得了解、越有信息密度或趋势价值。\n"
            f"摘要不超过 {self.config.max_length} 句话。\n"
            "请只输出严格 JSON，不要输出 Markdown、代码块或额外说明。\n"
            '格式：{"score": 8.5, "summary": "这里是摘要内容"}\n\n'
            f"{title_part}"
            f"内容：\n{content}"
        )

    def _build_score_prompt(self, news_item: NewsItem) -> str:
        """Build a prompt for scoring already-summarized items."""
        title_part = f"标题：{news_item.title}\n\n"
        content = news_item.content[:2000]
        return (
            "你是一个新闻情报筛选助手。\n"
            "请只根据下面的标题和内容，给出 0-10 的推荐分。\n"
            "分数越高，代表越值得了解、越有信息密度或趋势价值。\n"
            "请只输出严格 JSON，不要输出 Markdown、代码块或额外说明。\n"
            '格式：{"score": 8.5}\n\n'
            f"{title_part}"
            f"内容：\n{content}"
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

    def _parse_scored_summary(self, text: str) -> tuple[float | None, str]:
        """Parse a model response containing both score and summary."""
        text = self._clean_summary(text)
        payload = self._extract_json_payload(text)
        if payload is not None:
            score = self._normalize_score(self._coerce_score(payload.get("score")))
            summary = str(payload.get("summary") or "").strip()
            if summary:
                return score, summary

        score = self._extract_score_from_text(text)

        summary_match = re.search(r"(?:摘要|总结|summary)\s*[:：]\s*(.+)", text, flags=re.I | re.S)
        if summary_match:
            summary = summary_match.group(1).strip()
        else:
            summary = re.sub(r"(?:评分|推荐分|score|rating)\s*[:：]?\s*\d+(?:\.\d+)?(?:\s*/\s*10)?", "", text, flags=re.I)
            summary = summary.strip()

        return score, summary or text

    def _parse_score_only(self, text: str) -> float | None:
        """Parse a score-only model response."""
        text = self._clean_summary(text)
        payload = self._extract_json_payload(text)
        if payload is not None:
            score = self._normalize_score(self._coerce_score(payload.get("score")))
            if score is not None:
                return score
        return self._extract_score_from_text(text)

    @staticmethod
    def _extract_json_payload(text: str) -> dict | None:
        """Extract a JSON object from model text if one is present."""
        candidate_texts = [text]
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            candidate_texts.insert(0, match.group(0))

        for candidate in candidate_texts:
            try:
                payload = json.loads(candidate)
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                return payload
        return None

    @staticmethod
    def _extract_score_from_text(text: str) -> float | None:
        """Extract a 0-10 recommendation score from text."""
        patterns = [
            r"(?:评分|推荐分|精选分|价值分|score|rating)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:/|／)?\s*10?",
            r"(\d+(?:\.\d+)?)\s*(?:/|／)\s*10",
            r"(\d+(?:\.\d+)?)\s*分",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.I)
            if not match:
                continue
            value = float(match.group(1))
            if value > 10:
                value = value / 10 if value <= 100 else 10
            return max(0.0, min(10.0, value))
        return None

    @staticmethod
    def _normalize_score(value: float | None) -> float | None:
        """Clamp a score to the 0-10 range."""
        if value is None:
            return None
        if value > 10:
            value = value / 10 if value <= 100 else 10
        return max(0.0, min(10.0, value))

    @staticmethod
    def _coerce_score(value) -> float | None:
        """Coerce a loose score value into a float."""
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            match = re.search(r"\d+(?:\.\d+)?", str(value))
            return float(match.group(0)) if match else None

    async def summarize(self, news_item: NewsItem) -> Summary:
        """Generate one summary."""
        if news_item.metadata.get("pre_summarized"):
            score = news_item.metadata.get("score")
            content = news_item.content.strip() or news_item.title
            if score is None:
                prompt = self._build_score_prompt(news_item)
                response_text, token_usage = await self.llm.generate_with_usage(prompt)
                score = self._parse_score_only(response_text)
            else:
                token_usage = 0
            return Summary(
                original_url=news_item.url,
                summary=content.strip(),
                model=f"source:{news_item.source}",
                score=score,
                token_usage=token_usage,
                metadata={
                    "score": score,
                    "pre_summarized": True,
                    "source": news_item.source,
                    "source_priority": news_item.metadata.get("priority", 0),
                },
            )

        prompt = self._build_prompt(news_item)
        response_text, token_usage = await self.llm.generate_with_usage(prompt)
        score, summary_text = self._parse_scored_summary(response_text)
        if score is None:
            score = news_item.metadata.get("score")

        return Summary(
            original_url=news_item.url,
            summary=summary_text.strip(),
            model=self.llm.model_name,
            score=score,
            token_usage=token_usage,
            metadata={
                "score": score,
                "pre_summarized": False,
                "source": news_item.source,
                "source_priority": news_item.metadata.get("priority", 0),
            },
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
