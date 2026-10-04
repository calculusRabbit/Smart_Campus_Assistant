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

model = SentenceTransformer(
    EMBEDDING_MODEL,
    model_kwargs={"torch_dtype": "float16"},
)


def embed_chunk(chunks: list) -> np.ndarray:
    vectors = model.encode(
        chunks,
        show_progress_bar=True,
        truncate_dim=EMBEDDING_DIM,
        batch_size=1,
    )
    return vectors


def load_json(file_path: str, encoding: str = "utf-8") -> list:
    with open(file_path, encoding=encoding) as file:
        data = json.load(file)
    return data


def build_faiss_index(vectors):
    vectors = vectors.astype(np.float32) # base on doc
    emb_size = vectors.shape[1]
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(emb_size)

    # add vector
    index.add(vectors)
    return index


def main():
    data = load_json(CHUNKS_PATH, encoding="utf-8")

    chunks = []
    for item in data:
        chunks.append(item["chunk_text"])

    print("start embedding")
    vectors = embed_chunk(chunks)

    print("start build db")
    document_index = build_faiss_index(vectors)
    faiss.write_index(document_index, str(INDEX_PATH))

    print("Done: ", len(chunks))


if __name__ == "__main__":
    main()










