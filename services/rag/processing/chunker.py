import json
import os
from config import FILTERED_DIR, PAGES_CHUNKS_PATH, CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        if end < len(text):
            boundary = chunk.rfind(' ')
            if boundary != -1:
                chunk = chunk[:boundary]
        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)
        start += len(chunk) - CHUNK_OVERLAP
    return chunks


def main():
    input_file = os.path.join(FILTERED_DIR, "wsu_pages_clean.json")

    with open(input_file, encoding="utf-8") as f:
        pages = json.load(f)

    result = []
    for page in pages:
        for chunk in chunk_text(page["text"]):
            result.append({
                "source": "page",
                "url": page["url"],
                "title": page["title"],
                "chunk_text": chunk
            })

    os.makedirs("data", exist_ok=True)
    with open(PAGES_CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Done: {len(pages)} pages → {len(result)} chunks")


if __name__ == "__main__":
    main()
