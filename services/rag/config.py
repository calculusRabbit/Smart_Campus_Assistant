import os
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent
DATA_DIR = RAG_DIR / "data"

RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"

# models
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

GENERATION_MODEL = "qwen3-direct"
OLLAMA_URL = "http://host.docker.internal:11434"

# paths
CHUNKS_PATH = DATA_DIR / "chunks.json"
INDEX_PATH = DATA_DIR / "document_index.faiss"
RAW_DATA_PATH = DATA_DIR / "raw" / "wsu_pages_new.json"
FILTERED_DIR = DATA_DIR / "filtered"
ALL_URLS_PATH = DATA_DIR / "all_urls.jsonl"
EVENTS_PATH = DATA_DIR / "events.json"
CLUBS_PATH = DATA_DIR / "clubs.json"
PAGES_CHUNKS_PATH = DATA_DIR / "pages_chunks.json"
SHOCKERSYNC_EVENTS_PATH = DATA_DIR / "shockersync_events.json"

# calendar scraper
MAX_MISSES = 300 # stop after this many empty eIDs in a row
RETRIES = 3
BOOTSTRAP_EID = 20000 # where to start if no events are saved yet

# retrieval
TOP_K = 5

# chunking, these are in tokens (not characters) of the embedding model
# all-MiniLM-L6-v2 cuts off at 256 tokens so leave room for the page title that gets added to each chunk
CHUNK_SIZE    = 200
CHUNK_OVERLAP = 50
