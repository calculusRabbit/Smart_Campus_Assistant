import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer
from services.rag.config import DATA_DIR, EMBEDDING_MODEL, FILTERED_DIR, PAGES_CHUNKS_PATH, CHUNK_SIZE, CHUNK_OVERLAP


def make_splitter():
    # chunk size is counted in tokens with the embedding models own tokenizer
    # so if we change EMBEDDING_MODEL in config the chunks still fit
    tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
    return RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        tokenizer,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        # try paragraphs first, then lines, then sentences, then words
        separators=["\n\n", "\n", ". ", " ", ""],
        # keep the period with its own sentence, not at the start of the next chunk
        keep_separator="end"
    )


def chunk_page(splitter, title, text):
    # the crawler put "title - " in front of the text, take it off here
    # and add the title to every chunk so each one knows what page it is from
    prefix = title + " - "
    if text.startswith(prefix):
        text = text[len(prefix):]

    chunks = []
    for piece in splitter.split_text(text):
        chunks.append(prefix + piece)
    return chunks


def main():
    input_file = os.path.join(FILTERED_DIR, "wsu_pages_clean.json")

    with open(input_file, encoding="utf-8") as f:
        pages = json.load(f)

    splitter = make_splitter()

    result = []
    for page in pages:
        for chunk in chunk_page(splitter, page["title"], page["text"]):
            result.append({
                "source": "page",
                "url": page["url"],
                "title": page["title"],
                "chunk_text": chunk
            })

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PAGES_CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Done: {len(pages)} pages → {len(result)} chunks")


if __name__ == "__main__":
    main()
