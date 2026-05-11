"""Abstract base class for LLM clients."""

from abc import ABC, abstractmethod
from typing import Optional


class LLMClient(ABC):
    """Abstract base class for all LLM clients."""

    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.3,
        **kwargs,
    ):
        self.model_name = model_name
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt.

        Args:
            prompt: The input prompt text.
            **kwargs: Additional provider-specific arguments.

        Returns:
            Generated text string.
        """
        pass

    @abstractmethod
    async def generate_with_usage(self, prompt: str, **kwargs) -> tuple[str, int]:
        """Generate text and return token usage.

        Args:
            prompt: The input prompt text.
            **kwargs: Additional provider-specific arguments.

        Returns:
            Tuple of (generated text, token usage).
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'anthropic', 'ollama')."""
        pass

    async def close(self) -> None:
        """Clean up client resources when needed."""
        return None
