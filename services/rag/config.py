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
RAW_DATA_PATH     = "data/raw/wsu_pages_new.json"
FILTERED_DIR      = "data/filtered"
ALL_URLS_PATH     = "data/all_urls.jsonl"
EVENTS_PATH             = "data/events.json"
CLUBS_PATH              = "data/clubs.json"
PAGES_CHUNKS_PATH       = "data/pages_chunks.json"
SHOCKERSYNC_EVENTS_PATH = "data/shockersync_events.json"

# retrieval
TOP_K = 5

# chunking
CHUNK_SIZE    = 1000
CHUNK_OVERLAP = 150
