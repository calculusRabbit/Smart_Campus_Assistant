import httpx
import numpy as np

from services.rag.pipeline import is_bad_generation


def mock_retrieval(monkeypatch, pipeline):
    """Avoid loading the real embedding model and running a real FAISS search."""
    monkeypatch.setattr(
        pipeline,
        "embed_query",
        lambda _: np.zeros((1, 384), dtype=np.float32),
    )

    monkeypatch.setattr(
        pipeline,
        "search_similar",
        lambda index, vector, top_k: (
            np.array([0.9]),
            np.array([0]),
        ),
    )


def test_empty_generation_is_bad():
    assert is_bad_generation("") is True


def test_repetitive_generation_is_bad():
    answer = "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    assert is_bad_generation(answer) is True


def test_normal_generation_is_good():
    answer = (
        "The Japanese Culture Association provides opportunities "
        "for students interested in Japanese culture."
    )
    assert is_bad_generation(answer) is False


def test_bad_generation_retries_and_uses_second_response(monkeypatch):
    from services.rag import pipeline

    mock_retrieval(monkeypatch, pipeline)

    responses = iter(
        [
            "!!!!!!!!!!!!!!!!!!!!!!!!",
            "The Japanese Culture Association is a WSU student organization.",
        ]
    )

    def fake_generate_with_ollama(messages):
        return next(responses)

    monkeypatch.setattr(
        pipeline,
        "generate_with_ollama",
        fake_generate_with_ollama,
    )

    answer, sources = pipeline.query_RAG(
        "What is the Japanese Culture Association?",
        history=[],
    )

    assert answer == "The Japanese Culture Association is a WSU student organization."
    assert "[1]" in sources


def test_two_bad_generations_return_fallback(monkeypatch):
    from services.rag import pipeline

    mock_retrieval(monkeypatch, pipeline)

    call_count = 0

    def fake_generate_with_ollama(messages):
        nonlocal call_count
        call_count += 1
        return "!!!!!!!!!!!!!!!!!!!!!!!!"

    monkeypatch.setattr(
        pipeline,
        "generate_with_ollama",
        fake_generate_with_ollama,
    )

    answer, sources = pipeline.query_RAG(
        "What is the Japanese Culture Association?",
        history=[],
    )

    assert answer == (
        "I couldn't generate a reliable answer right now. "
        "Please try asking your question again."
    )
    assert call_count == 2
    assert "[1]" in sources


def test_network_failure_returns_friendly_message(monkeypatch):
    from services.rag import pipeline

    mock_retrieval(monkeypatch, pipeline)

    def fake_generate_with_ollama(messages):
        raise httpx.ConnectError("Ollama service unavailable")

    monkeypatch.setattr(
        pipeline,
        "generate_with_ollama",
        fake_generate_with_ollama,
    )

    answer, sources = pipeline.query_RAG(
        "What is the Japanese Culture Association?",
        history=[],
    )

    assert answer == (
        "I found relevant campus information, but the AI generation "
        "service is temporarily unavailable. Please try again in a moment."
    )
    assert "[1]" in sources


def test_ollama_http_error_returns_friendly_message(monkeypatch):
    from services.rag import pipeline

    mock_retrieval(monkeypatch, pipeline)

    def fake_generate_with_ollama(messages):
        request = httpx.Request(
            "POST",
            "http://host.docker.internal:11434/api/chat",
        )
        response = httpx.Response(
            status_code=500,
            request=request,
        )
        raise httpx.HTTPStatusError(
            "Ollama generation service unavailable",
            request=request,
            response=response,
        )

    monkeypatch.setattr(
        pipeline,
        "generate_with_ollama",
        fake_generate_with_ollama,
    )

    answer, sources = pipeline.query_RAG(
        "What is the purpose of ShockerSync?",
        history=[],
    )

    assert answer == (
        "I found relevant campus information, but the AI generation "
        "service is temporarily unavailable. Please try again in a moment."
    )
    assert "[1]" in sources


def test_conversation_history_is_included(monkeypatch):
    from services.rag import pipeline

    mock_retrieval(monkeypatch, pipeline)

    captured_messages = []

    def fake_generate_with_ollama(messages):
        captured_messages.extend(messages)
        return "The Japan Festival is a WSU event."

    monkeypatch.setattr(
        pipeline,
        "generate_with_ollama",
        fake_generate_with_ollama,
    )

    answer, sources = pipeline.query_RAG(
        "When is it?",
        history=[
            (
                "Tell me about the Japan Festival.",
                "The Japan Festival is an event at WSU.",
            )
        ],
    )

    assert captured_messages[1] == {
        "role": "user",
        "content": "Tell me about the Japan Festival.",
    }

    assert captured_messages[2] == {
        "role": "assistant",
        "content": "The Japan Festival is an event at WSU.",
    }

    assert answer == "The Japan Festival is a WSU event."
    assert "[1]" in sources