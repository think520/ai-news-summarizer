"""OpenAI GPT client implementation."""

from typing import Optional

from openai import AsyncOpenAI

from ai_news_summarizer.llm.base import LLMClient


class OpenAIClient(LLMClient):
    """OpenAI GPT client using the official SDK."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.3,
        **kwargs,
    ):
        super().__init__(model_name, api_key, max_tokens, temperature)
        self.client = AsyncOpenAI(api_key=api_key, **kwargs)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI's chat completion API."""
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    async def generate_with_usage(self, prompt: str, **kwargs) -> tuple[str, int]:
        """Generate text and return token usage."""
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            **kwargs,
        )
        usage = response.usage
        token_usage = (usage.prompt_tokens + usage.completion_tokens) if usage else 0
        return response.choices[0].message.content or "", token_usage

    async def close(self) -> None:
        """Close the underlying SDK client."""
        await self.client.close()
