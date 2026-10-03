from sentence_transformers import SentenceTransformer
import numpy as np
import json
import faiss
from services.rag.config import (
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    INDEX_PATH,
    CHUNKS_PATH,
)

model = None

def get_embedding_model():
    global model

    if model is None:
        print("Loading embedding model...")
        model = SentenceTransformer(EMBEDDING_MODEL)
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
    faiss.normalize_L2(vector)  # normalize since in document index we also already normalize all vectors
    return vector

def search_similar(index_document, query_vector, top_k=5):
    # use cosine similarity here:
    distances, indices = index_document.search(query_vector, k=top_k)
    return distances[0], indices[0] # get flat list 


def main():
    index = faiss.read_index(INDEX_PATH)

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


