from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

from app.ai.providers.base import BaseLLMProvider
from app.core.config import settings


class ClaudeProvider(BaseLLMProvider):
    """
    LLM provider using FreeLLMAPI's OpenAI-compatible endpoint.

    Despite the legacy class and filename, this currently connects
    to NVIDIA Nemotron through FreeLLMAPI.
    """

    def __init__(self):
        self.model = settings.CLAUDE_MODEL
        self.base_url = f"{settings.ANTHROPIC_BASE_URL.rstrip('/')}/v1"
        self.api_key = settings.ANTHROPIC_API_KEY

    def get_chat_model(self) -> BaseChatModel:
        if not self.api_key:
            raise ValueError("FreeLLMAPI API key is not configured.")

        return ChatOpenAI(
            model=self.model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=0,
            max_tokens=3500,
            timeout=60,
            max_retries=1,
        )