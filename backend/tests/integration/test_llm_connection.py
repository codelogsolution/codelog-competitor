from app.ai.providers.claude_provider import ClaudeProvider


def test_llm_provider_initialization():
    provider = ClaudeProvider()
    llm = provider.get_chat_model()

    assert llm is not None

    print("\nLLM provider initialized successfully.")
    print("Model:", provider.model)
    print("Base URL:", provider.base_url)


def test_llm_actual_response():
    provider = ClaudeProvider()
    llm = provider.get_chat_model()

    response = llm.invoke(
        "Reply with exactly: KOMP LLM connection successful"
    )

    print("\nActual LLM Response:", response.content)

    assert response.content
    assert "KOMP" in str(response.content)