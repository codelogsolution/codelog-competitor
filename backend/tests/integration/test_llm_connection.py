import os

import pytest

from app.ai.providers.claude_provider import ClaudeProvider
from app.core.config import settings


RUN_LIVE_LLM_TESTS = os.getenv("RUN_LIVE_LLM_TESTS", "").strip().lower() == "true"
pytestmark = pytest.mark.skipif(
    not RUN_LIVE_LLM_TESTS or not settings.ANTHROPIC_API_KEY,
    reason="Set RUN_LIVE_LLM_TESTS=true and configure ANTHROPIC_API_KEY to run live provider tests.",
)


def test_llm_provider_initialization():
    provider = ClaudeProvider()
    llm = provider.get_chat_model()
    assert llm is not None


def test_llm_actual_response():
    provider = ClaudeProvider()
    llm = provider.get_chat_model()
    response = llm.invoke("Reply with exactly: KOMP LLM connection successful")
    assert response.content
    assert "KOMP" in str(response.content)
