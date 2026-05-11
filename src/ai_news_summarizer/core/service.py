"""Shared application services for CLI and web entry points."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from ai_news_summarizer.config.loader import ConfigLoader
from ai_news_summarizer.core.processor import NewsProcessor
from ai_news_summarizer.llm import AnthropicClient, OllamaClient, OpenAIClient
from ai_news_summarizer.llm.base import LLMClient
from ai_news_summarizer.models.schemas import LLMConfig, SourceConfig, SummaryConfig


LLM_CLIENTS: dict[str, type[LLMClient]] = {
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "ollama": OllamaClient,
}


@dataclass(slots=True)
class PreparedProcessor:
    """A configured processor together with resolved metadata."""

    processor: NewsProcessor
    provider: str
    summary_config: SummaryConfig


class AppService:
    """Factory methods shared by multiple entry points."""

    @staticmethod
    def load_config(config_path: str | Path) -> dict[str, Any]:
        return ConfigLoader(config_path).load()

    @staticmethod
    def resolve_provider(config: dict[str, Any], provider_override: str | None = None) -> str:
        if provider_override:
            return provider_override
        return str(config.get("llm", {}).get("default", "openai"))

    @staticmethod
    def get_summary_config(config: dict[str, Any]) -> SummaryConfig:
        return SummaryConfig(**config.get("summary", {}))

    @staticmethod
    def get_llm_config(config: dict[str, Any], provider: str) -> LLMConfig:
        llm_config_dict = config.get("llm", {}).get("providers", {}).get(provider)
        if not llm_config_dict:
            raise ValueError(f"Missing configuration for LLM provider: {provider}")
        return LLMConfig(**llm_config_dict)

    @staticmethod
    def create_llm_client(provider: str, config: LLMConfig) -> LLMClient:
        client_class = LLM_CLIENTS.get(provider)
        if client_class is None:
            raise ValueError(f"Unknown LLM provider: {provider}")

        kwargs: dict[str, Any] = {
            "model_name": config.model,
            "api_key": config.api_key,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }
        if config.base_url:
            kwargs["base_url"] = config.base_url

        return client_class(**kwargs)

    @staticmethod
    def normalize_source_configs(raw_sources: Sequence[dict[str, Any]]) -> list[SourceConfig]:
        normalized: list[SourceConfig] = []
        for raw in raw_sources:
            source_type = raw["type"]
            name = raw["name"]
            params = dict(raw.get("params", {}))

            if not params:
                params = {
                    key: value
                    for key, value in raw.items()
                    if key not in {"type", "name", "params"}
                }

            normalized.append(SourceConfig(type=source_type, name=name, params=params))
        return normalized

    @classmethod
    def build_processor(
        cls,
        config: dict[str, Any],
        provider_override: str | None = None,
        source_names: Iterable[str] | None = None,
        raw_sources: Sequence[dict[str, Any]] | None = None,
    ) -> PreparedProcessor:
        provider = cls.resolve_provider(config, provider_override)
        llm_config = cls.get_llm_config(config, provider)
        llm_client = cls.create_llm_client(provider, llm_config)
        summary_config = cls.get_summary_config(config)

        source_entries = list(raw_sources) if raw_sources is not None else list(config.get("sources", []))
        if source_names:
            allowed = set(source_names)
            source_entries = [entry for entry in source_entries if entry.get("name") in allowed]

        sources_config = cls.normalize_source_configs(source_entries)
        processor = NewsProcessor.from_config(sources_config, llm_client, summary_config)
        return PreparedProcessor(processor=processor, provider=provider, summary_config=summary_config)
