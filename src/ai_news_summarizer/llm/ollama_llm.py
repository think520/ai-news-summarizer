"""Ollama local LLM client implementation."""

from typing import Optional

import httpx

from ai_news_summarizer.llm.base import LLMClient


class OllamaClient(LLMClient):
    """Ollama local model client."""

    def __init__(
        self,
        model_name: str = "llama3",
        api_key: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.3,
        base_url: str = "http://localhost:11434",
        **kwargs,
    ):
        super().__init__(model_name, api_key, max_tokens, temperature)
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
        return self._client

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama's generate API."""
        client = await self._get_client()
        response = await client.post(
            "/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
                **kwargs,
            },
        )
        response.raise_for_status()
        return response.json().get("response", "")

    async def generate_with_usage(self, prompt: str, **kwargs) -> tuple[str, int]:
        """Generate text and return token usage (not supported by Ollama, returns 0)."""
        text = await self.generate(prompt, **kwargs)
        return text, 0

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
