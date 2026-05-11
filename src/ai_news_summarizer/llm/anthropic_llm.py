"""Anthropic Claude client implementation."""

from typing import Optional

from anthropic import AsyncAnthropic

from ai_news_summarizer.llm.base import LLMClient


class AnthropicClient(LLMClient):
    """Anthropic Claude client using the official SDK."""

    def __init__(
        self,
        model_name: str = "claude-3-haiku-20240307",
        api_key: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.3,
        **kwargs,
    ):
        super().__init__(model_name, api_key, max_tokens, temperature)
        self.client = AsyncAnthropic(api_key=api_key, **kwargs)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Anthropic's messages API."""
        response = await self.client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return response.content[0].text if response.content else ""

    async def generate_with_usage(self, prompt: str, **kwargs) -> tuple[str, int]:
        """Generate text and return token usage."""
        response = await self.client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        usage = response.usage
        token_usage = (usage.input_tokens + usage.output_tokens) if usage else 0
        return response.content[0].text if response.content else "", token_usage

    async def close(self) -> None:
        """Close the underlying SDK client."""
        await self.client.close()
