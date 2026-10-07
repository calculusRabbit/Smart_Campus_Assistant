from services.rag.pipeline import is_bad_generation


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
    from types import SimpleNamespace

    import numpy as np

    from services.rag import pipeline

    # Avoid running the real embedding model.
    monkeypatch.setattr(
        pipeline,
        "embed_query",
        lambda _: np.zeros((1, 384), dtype=np.float32),
    )

    # Avoid running the real FAISS search.
    monkeypatch.setattr(
        pipeline,
        "search_similar",
        lambda index, vector, top_k: (
            np.array([0.9]),
            np.array([0]),
        ),
    )

    bad_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="!!!!!!!!!!!!!!!!!!!!!!!!")
            )
        ]
    )

    good_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="The Japanese Culture Association is a WSU student organization."
                )
            )
        ]
    )

    responses = iter([bad_response, good_response])

    def fake_chat_completion(**kwargs):
        return next(responses)

    monkeypatch.setattr(
        pipeline.client,
        "chat_completion",
        fake_chat_completion,
    )

    answer, sources = pipeline.query_RAG(
        "What is the Japanese Culture Association?",
        history=[],
    )

    assert answer == (
        "The Japanese Culture Association is a WSU student organization."
    )
    assert "[1]" in sources

def test_two_bad_generations_return_fallback(monkeypatch):
    from types import SimpleNamespace

    import numpy as np

    from services.rag import pipeline

    # Avoid loading the real embedding model.
    monkeypatch.setattr(
        pipeline,
        "embed_query",
        lambda _: np.zeros((1, 384), dtype=np.float32),
    )

    # Avoid running the real FAISS search.
    monkeypatch.setattr(
        pipeline,
        "search_similar",
        lambda index, vector, top_k: (
            np.array([0.9]),
            np.array([0]),
        ),
    )

    call_count = 0

    def fake_chat_completion(**kwargs):
        nonlocal call_count
        call_count += 1

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="!!!!!!!!!!!!!!!!!!!!!!!!"
                    )
                )
            ]
        )

    monkeypatch.setattr(
        pipeline.client,
        "chat_completion",
        fake_chat_completion,
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
    import httpx
    import numpy as np

    from services.rag import pipeline

    # Avoid loading the real embedding model.
    monkeypatch.setattr(
        pipeline,
        "embed_query",
        lambda _: np.zeros((1, 384), dtype=np.float32),
    )

    # Avoid running the real FAISS search.
    monkeypatch.setattr(
        pipeline,
        "search_similar",
        lambda index, vector, top_k: (
            np.array([0.9]),
            np.array([0]),
        ),
    )

    def fake_chat_completion(**kwargs):
        raise httpx.ConnectError("AI service unavailable")

    monkeypatch.setattr(
        pipeline.client,
        "chat_completion",
        fake_chat_completion,
    )

    answer, sources = pipeline.query_RAG(
        "What is the Japanese Culture Association?",
        history=[],
    )

    assert answer == (
        "I'm having trouble connecting to the AI service right now. "
        "Please try again in a moment."
    )
    assert "[1]" in sources

def test_conversation_history_is_included(monkeypatch):
    from types import SimpleNamespace

    import numpy as np

    from services.rag import pipeline

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

    captured_messages = []

    def fake_chat_completion(**kwargs):
        captured_messages.extend(kwargs["messages"])

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="The Japan Festival is a WSU event."
                    )
                )
            ]
        )

    monkeypatch.setattr(
        pipeline.client,
        "chat_completion",
        fake_chat_completion,
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