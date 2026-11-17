from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings


class LLMProvider:
    """Create the configured chat model; provider choice is environment-driven."""

    def get_chat_model(self) -> Any:
        provider = settings.LLM_PROVIDER.strip().lower()

        if provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is not configured.")
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=settings.LLM_MODEL,
                api_key=settings.ANTHROPIC_API_KEY,
                base_url=settings.ANTHROPIC_BASE_URL or None,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                timeout=60,
                max_retries=1,
            )

        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not configured.")
            from langchain_openai import ChatOpenAI

            kwargs = {
                "model": settings.LLM_MODEL,
                "api_key": settings.OPENAI_API_KEY,
                "temperature": settings.LLM_TEMPERATURE,
                "max_tokens": settings.LLM_MAX_TOKENS,
                "timeout": 60,
                "max_retries": 1,
            }
            if settings.OPENAI_BASE_URL:
                kwargs["base_url"] = settings.OPENAI_BASE_URL
            return ChatOpenAI(**kwargs)

        if provider == "vertex_ai":
            if not settings.GOOGLE_CLOUD_PROJECT:
                raise ValueError("GOOGLE_CLOUD_PROJECT is not configured.")
            from langchain_google_vertexai import ChatVertexAI

            return ChatVertexAI(
                model_name=settings.LLM_MODEL,
                project=settings.GOOGLE_CLOUD_PROJECT,
                location=settings.GOOGLE_CLOUD_LOCATION,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
            )

        raise ValueError(
            "Unsupported LLM_PROVIDER. Use anthropic, openai, or vertex_ai."
        )


# Backward-compatible import name used by the existing BattlecardService/tests.
class ClaudeProvider(LLMProvider):
    """Legacy alias; provider is selected by LLM_PROVIDER, not this class name."""
    pass
