"""Tests for LLM client modules."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from ai_news_summarizer.llm.openai_llm import OpenAIClient
from ai_news_summarizer.llm.anthropic_llm import AnthropicClient
from ai_news_summarizer.llm.ollama_llm import OllamaClient


class TestOpenAIClient:
    """Tests for OpenAI client."""

    @pytest.fixture
    def mock_response(self):
        """Create a mock OpenAI response."""
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "Test summary"
        response.usage = MagicMock()
        response.usage.prompt_tokens = 100
        response.usage.completion_tokens = 50
        return response

    @pytest.mark.asyncio
    async def test_generate_returns_text(self, mock_response):
        """Test that generate returns the generated text."""
        client = OpenAIClient(model_name="gpt-4", api_key="test-key")

        with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            result = await client.generate("Test prompt")
            assert result == "Test summary"

    @pytest.mark.asyncio
    async def test_generate_with_usage(self, mock_response):
        """Test that generate_with_usage returns text and token count."""
        client = OpenAIClient(model_name="gpt-4", api_key="test-key")

        with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            text, usage = await client.generate_with_usage("Test prompt")
            assert text == "Test summary"
            assert usage == 150

    def test_provider_name(self):
        """Test provider name is correct."""
        client = OpenAIClient(model_name="gpt-4", api_key="test-key")
        assert client.provider_name == "openai"


class TestAnthropicClient:
    """Tests for Anthropic client."""

    @pytest.fixture
    def mock_response(self):
        """Create a mock Anthropic response."""
        response = MagicMock()
        response.content = [MagicMock()]
        response.content[0].text = "Test summary"
        response.usage = MagicMock()
        response.usage.input_tokens = 100
        response.usage.output_tokens = 50
        return response

    @pytest.mark.asyncio
    async def test_generate_returns_text(self, mock_response):
        """Test that generate returns the generated text."""
        client = AnthropicClient(model_name="claude-3", api_key="test-key")

        with patch.object(client.client.messages, "create", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            result = await client.generate("Test prompt")
            assert result == "Test summary"

    def test_provider_name(self):
        """Test provider name is correct."""
        client = AnthropicClient(model_name="claude-3", api_key="test-key")
        assert client.provider_name == "anthropic"


class TestOllamaClient:
    """Tests for Ollama client."""

    @pytest.fixture
    def mock_response(self):
        """Create a mock Ollama response."""
        response = MagicMock()
        response.json.return_value = {"response": "Test summary"}
        return response

    @pytest.mark.asyncio
    async def test_generate_returns_text(self, mock_response):
        """Test that generate returns the generated text."""
        client = OllamaClient(model_name="llama3", base_url="http://localhost:11434")

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        client._client = mock_client

        result = await client.generate("Test prompt")
        assert result == "Test summary"

    def test_provider_name(self):
        """Test provider name is correct."""
        client = OllamaClient(model_name="llama3")
        assert client.provider_name == "ollama"
