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