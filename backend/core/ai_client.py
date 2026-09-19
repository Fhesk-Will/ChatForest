from typing import AsyncGenerator

from .providers.openai_compat import OpenAICompatProvider
from .providers.base import BaseProvider


def get_provider(provider_config: dict) -> BaseProvider:
    provider_type = provider_config.get("type", "openai_compat")
    if provider_type == "openai_compat":
        return OpenAICompatProvider(
            base_url=provider_config["base_url"],
            api_key=provider_config["api_key"],
        )
    raise ValueError(f"Unknown provider type: {provider_type}")
