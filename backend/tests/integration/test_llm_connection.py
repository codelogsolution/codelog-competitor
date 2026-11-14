import pytest

from app.ai.providers.claude_provider import ClaudeProvider
from app.core.config import settings


pytestmark = pytest.mark.skipif(
    not settings.ANTHROPIC_API_KEY,
    reason="ANTHROPIC_API_KEY is not configured",
)


def test_llm_provider_initialization():
    provider = ClaudeProvider()
    llm = provider.get_chat_model()

    assert llm is not None


def test_llm_actual_response():
    provider = ClaudeProvider()
    llm = provider.get_chat_model()

    response = llm.invoke(
        "Reply with exactly: KOMP LLM connection successful"
    )

    assert response.content
    assert "KOMP" in str(response.content)