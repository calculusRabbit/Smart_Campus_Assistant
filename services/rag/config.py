from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent
DATA_DIR = RAG_DIR / "data"

RAG_ENABLED = False

# models
EMBEDDING_MODEL  = "Qwen/Qwen3-Embedding-4B"
EMBEDDING_DIM = 384
JUDGE_MODEL      = "meta-llama/Llama-3.1-8B-Instruct"
GENERATION_MODEL = "Qwen/Qwen2.5-14B-Instruct"

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
