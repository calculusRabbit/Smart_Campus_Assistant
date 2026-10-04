import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from services.rag.config import (
    CHUNKS_PATH,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    INDEX_PATH,
)

model = None

def get_embedding_model():
    global model

    if model is None:
        print("Loading embedding model...")
        model = SentenceTransformer(
            EMBEDDING_MODEL,
            model_kwargs={"torch_dtype": "float16"},
        )
        print("Embedding model loaded")

    return model

def embed_query(user_input: str) -> np.ndarray:
    embedding_model = get_embedding_model()
    vector = embedding_model.encode(
        user_input,
        truncate_dim=EMBEDDING_DIM
    )
    vector = vector.astype(np.float32)
    vector = vector.reshape(1, -1)  # reshape to 2D for FAISS
    # Normalize because document vectors are also normalized.
    faiss.normalize_L2(vector)
    return vector

def search_similar(index_document, query_vector, top_k=5):
    # use cosine similarity here:
    distances, indices = index_document.search(query_vector, k=top_k)
    return distances[0], indices[0] # get flat list 


def main():
    index = faiss.read_index(str(INDEX_PATH))

    with open(CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)

    # test a query
    query = "Japan festival"
    query_vector = embed_query(query)
    distances, indices = search_similar(index, query_vector, top_k=5)


    for i, actual_idx in enumerate(indices):
        print("COSINE SIMILARITY SCORE: ", distances[i])
        print(chunks[actual_idx]["chunk_text"])
        print("\n------------------------------------------------------------------------------------------\n")



if __name__ == "__main__":
    main()


