import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from services.rag.config import ALL_EVENTS_PATH, EVENTS_EMBEDDING_MODEL, EVENTS_INDEX_PATH

# makes a faiss index of all_events.json for the recommendations
# the vector at position i is the event at position i in all_events.json
# run merge_events.py first and run this again every time all_events.json changes


def main():
    with open(ALL_EVENTS_PATH, encoding="utf-8") as f:
        events = json.load(f)

    if len(events) == 0:
        print("no events in all_events.json, nothing to index")
        return

    texts = []
    for event in events:
        texts.append(event["embed_text"])

    print("embedding", len(texts), "events with", EVENTS_EMBEDDING_MODEL)
    model = SentenceTransformer(EVENTS_EMBEDDING_MODEL)
    vectors = model.encode(texts, batch_size=32, show_progress_bar=True)

    # normalize so inner product is the same as cosine similarity
    vectors = vectors.astype(np.float32)
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(EVENTS_INDEX_PATH))

    print("done:", index.ntotal, "events in the index, vector size", vectors.shape[1])


if __name__ == "__main__":
    main()
