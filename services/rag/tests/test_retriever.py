import numpy as np

from services.rag import retriever


def test_embed_query_returns_normalized_float32_vector(monkeypatch):
    class FakeEmbeddingModel:
        def encode(self, user_input, truncate_dim):
            assert user_input == "Japan Festival"
            assert truncate_dim == retriever.EMBEDDING_DIM

            vector = np.zeros(retriever.EMBEDDING_DIM, dtype=np.float64)
            vector[0] = 3.0
            vector[1] = 4.0
            return vector

    monkeypatch.setattr(
        retriever,
        "get_embedding_model",
        lambda: FakeEmbeddingModel(),
    )

    vector = retriever.embed_query("Japan Festival")

    assert vector.shape == (1, retriever.EMBEDDING_DIM)
    assert vector.dtype == np.float32
    assert np.isclose(np.linalg.norm(vector), 1.0)


def test_search_similar_returns_flat_results():
    class FakeIndex:
        def search(self, query_vector, k):
            assert k == 2

            distances = np.array([[0.95, 0.80]], dtype=np.float32)
            indices = np.array([[4, 7]])

            return distances, indices

    query_vector = np.zeros(
        (1, retriever.EMBEDDING_DIM),
        dtype=np.float32,
    )

    distances, indices = retriever.search_similar(
        FakeIndex(),
        query_vector,
        top_k=2,
    )

    assert distances.shape == (2,)
    assert indices.shape == (2,)
    assert np.allclose(distances, [0.95, 0.80])
    assert np.array_equal(indices, [4, 7])

import numpy as np

from services.rag import retriever


def test_embedding_model_is_loaded_once(monkeypatch):
    fake_model = object()
    calls = []

    def fake_sentence_transformer(name, **kwargs):
        calls.append(name)
        return fake_model

    monkeypatch.setattr(retriever, "model", None)
    monkeypatch.setattr(
        retriever, "SentenceTransformer", fake_sentence_transformer
    )

    first = retriever.get_embedding_model()
    second = retriever.get_embedding_model()

    assert first is fake_model
    assert second is fake_model
    assert len(calls) == 1
    assert calls[0] == retriever.EMBEDDING_MODEL


def test_embed_query_normalizes_vector(monkeypatch):
    class FakeEmbeddingModel:
        def encode(self, text, truncate_dim):
            assert text == "Japan Festival"
            assert truncate_dim == 384

            vector = np.zeros(384, dtype=np.float64)
            vector[0] = 3.0
            vector[1] = 4.0
            return vector

    monkeypatch.setattr(
        retriever,
        "get_embedding_model",
        lambda: FakeEmbeddingModel(),
    )

    result = retriever.embed_query("Japan Festival")

    assert result.shape == (1, 384)
    assert result.dtype == np.float32
    assert np.isclose(np.linalg.norm(result), 1.0)
    assert np.isclose(result[0, 0], 0.6)
    assert np.isclose(result[0, 1], 0.8)


def test_search_similar_returns_flat_results():
    class FakeIndex:
        def search(self, vector, k):
            assert vector.shape == (1, 384)
            assert k == 3

            distances = np.array([[0.95, 0.85, 0.75]])
            indices = np.array([[4, 2, 1]])
            return distances, indices

    query_vector = np.zeros((1, 384), dtype=np.float32)

    distances, indices = retriever.search_similar(
        FakeIndex(),
        query_vector,
        top_k=3,
    )

    assert distances.tolist() == [0.95, 0.85, 0.75]
    assert indices.tolist() == [4, 2, 1]