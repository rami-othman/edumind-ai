"""Provider-level LLM service abstraction."""

from __future__ import annotations

from app.config import Settings, get_settings
from app.services.llm.ollama_client import OllamaChatClient


class UnsupportedLLMProviderError(Exception):
    """Raised when the configured LLM provider is not implemented."""


def get_llm_client(settings: Settings | None = None) -> OllamaChatClient:
    """Return the configured LLM client."""

    active_settings = settings or get_settings()
    provider = active_settings.llm_provider.lower()

    if provider == "ollama":
        return OllamaChatClient(
            base_url=getattr(active_settings, "ollama_llm_base_url", None)
            or active_settings.ollama_base_url,
            model=active_settings.ollama_llm_model,
            api_key=getattr(active_settings, "ollama_api_key", None),
        )

    # TODO: Add additional LLM providers in a later milestone.
    raise UnsupportedLLMProviderError(f"Unsupported LLM provider: {provider}")


def generate_answer(
    system_prompt: str,
    user_prompt: str,
    settings: Settings | None = None,
    client: OllamaChatClient | None = None,
) -> str:
    """Generate an answer using the configured or injected LLM client."""

    active_client = client or get_llm_client(settings)
    return active_client.generate(system_prompt, user_prompt)
