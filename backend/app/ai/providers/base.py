from abc import ABC, abstractmethod

from langchain_core.language_models.chat_models import BaseChatModel


class BaseLLMProvider(ABC):
    """
    Common interface for all LLM providers.

    Every provider must implement get_chat_model().
    """

    @abstractmethod
    def get_chat_model(self) -> BaseChatModel:
        """
        Return a configured LangChain chat model.
        """
        pass