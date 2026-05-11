"""Configuration loader with environment variable support."""

import os
import re
from pathlib import Path
from typing import Any

import yaml


class ConfigLoader:
    """Loads and parses YAML configuration files with env var support."""

    ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)

    def load(self) -> dict[str, Any]:
        """Load configuration from YAML file.

        Resolves ${ENV_VAR} patterns with environment variables.

        Returns:
            Parsed configuration dictionary.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self._resolve_env_vars(config)
        return config

    def _resolve_env_vars(self, obj: Any) -> Any:
        """Recursively resolve ${ENV_VAR} patterns in config."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._resolve_env_vars(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = self._resolve_env_vars(item)
        elif isinstance(obj, str):
            return self.ENV_VAR_PATTERN.sub(
                lambda match: os.getenv(match.group(1), match.group(0)),
                obj,
            )
        return obj
