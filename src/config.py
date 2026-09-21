from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"


# LLM
LLM_MODEL = "deepseek-v4-flash"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"


# Embedding
EMBEDDING_MODEL = "qwen3-embedding:4b"
OLLAMA_BASE_URL = "http://localhost:11434"


# RAG
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
RETRIEVAL_K = 3

CHROMA_COLLECTION = "travel_knowledge"

# CITY
SUPPORTED_CITIES = [
    "queenstown",
    "auckland"
]

# Weather
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_FORECAST_DAYS = 16


MRTE_RAW_PATH = (
    DATA_DIR
    / "raw"
    / "Region-series.xlsx"
)

MRTE_CLEAN_PATH = (
    DATA_DIR
    / "processed"
    / "Region-series.csv"
)

# Places
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"

OVERPASS_URLS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

PLACES_SEARCH_RADIUS = 5000
PLACES_RESULT_LIMIT = 10

# =========================================================
# RAG reranking
# =========================================================

USE_RERANKER = True

RERANK_CANDIDATE_K = 12


# =========================================================
# Dissertation RAG evaluation
# =========================================================

DISSERTATION_SOURCE_DIR = (
    Path("data")
    / "rag_eval"
    / "source"
)

DISSERTATION_VECTOR_STORE_DIR = (
    Path("data")
    / "rag_eval"
    / "dissertation_vector_store"
)

DISSERTATION_CHROMA_COLLECTION = (
    "dissertation_eval"
)

DISSERTATION_RETRIEVAL_K = 5