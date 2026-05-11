"""Data models and schemas using Pydantic."""

from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl, field_validator


class NewsItem(BaseModel):
    """Represents a single news article or item."""

    id: str = Field(..., description="Unique identifier for the news item")
    title: str = Field(..., description="Title of the news article")
    content: str = Field(..., description="Full text content of the article")
    url: Optional[HttpUrl] = Field(None, description="URL of the original article")
    source: str = Field(..., description="Name of the news source")
    published_at: Optional[datetime] = Field(None, description="Publication date")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @field_validator("id", mode="before")
    @classmethod
    def generate_id_if_empty(cls, v: str) -> str:
        if not v:
            return f"news-{datetime.now().timestamp()}"
        return v


class Summary(BaseModel):
    """Represents an AI-generated summary of a news item."""

    original_url: Optional[HttpUrl] = Field(None, description="URL of the original article")
    summary: str = Field(..., description="Generated summary text")
    model: str = Field(..., description="LLM model used for generation")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    token_usage: Optional[int] = Field(None, description="Token usage for this generation")
    metadata: dict = Field(default_factory=dict, description="Additional summary metadata")


class SourceConfig(BaseModel):
    """Configuration for a news source."""

    type: str = Field(..., description="Source type: rss, scraper, api, local")
    name: str = Field(..., description="Friendly name for this source")
    params: dict = Field(default_factory=dict, description="Source-specific parameters")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {"rss", "scraper", "api", "local"}
        if v not in valid_types:
            raise ValueError(f"Source type must be one of {valid_types}")
        return v


class SummaryConfig(BaseModel):
    """Configuration for summary generation."""

    max_length: int = Field(5, description="Maximum number of sentences in summary")
    style: str = Field("concise", description="Summary style: concise, informative, detailed")
    include_title: bool = Field(True, description="Whether to include title in summary")
    language: str = Field("zh", description="Target language for summary")


class LLMConfig(BaseModel):
    """Configuration for an LLM provider."""

    model: str = Field(..., description="Model name or identifier")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    max_tokens: int = Field(500, description="Maximum tokens to generate")
    temperature: float = Field(0.3, ge=0.0, le=2.0, description="Sampling temperature")
    base_url: Optional[str] = Field(None, description="Custom base URL (for Ollama/proxies)")


class AppConfig(BaseModel):
    """Top-level application configuration."""

    app_name: str = Field("AI News Summarizer", description="Application name")
    version: str = Field("1.0.0", description="Application version")
    log_level: str = Field("INFO", description="Logging level")

    sources: list[SourceConfig] = Field(default_factory=list, description="News source configurations")
    llm: dict[str, LLMConfig] = Field(default_factory=dict, description="LLM provider configurations")
    summary: SummaryConfig = Field(default_factory=SummaryConfig, description="Summary generation config")
    default_llm: str = Field("openai", description="Default LLM provider to use")
