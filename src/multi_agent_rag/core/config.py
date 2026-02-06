import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Application Settings
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")  # nosec
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_RELOAD = os.getenv("APP_RELOAD", "true").lower() == "true"
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "https://mushfiq.xyz",
]

# Models
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
SEARCH_MODEL = os.getenv("SEARCH_MODEL", "gpt-4o-mini")
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "gpt-4o-mini")
CODER_MODEL = os.getenv("CODER_MODEL", "gpt-4o-mini")
VECTOR_MODEL = os.getenv("VECTOR_MODEL", "text-embedding-3-small")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# DB Settings (PostgreSQL)
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "multi_agent_rag")

# Construct DATABASE_URL if not explicitly provided
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

DB_MAX_RETRIES = int(os.getenv("DB_MAX_RETRIES", "5"))
DB_RETRY_DELAY = int(os.getenv("DB_RETRY_DELAY", "5"))

# Vector DB Settings (ChromaDB)
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Storage Settings
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
UPLOAD_CLEANUP = os.getenv("UPLOAD_CLEANUP", "true").lower() == "true"

# Cache Settings (Redis Stack)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24 hours
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"

# Cache prefixes
CACHE_PREFIX_RESEARCH = "res:"
CACHE_PREFIX_VECTOR = "vec:"
CACHE_PREFIX_RESPONSE = "rsp:"
CACHE_PREFIX_EMBEDDINGS = "emb:"

# Cache invalidation settings
CACHE_INVALIDATE_ON_KB_UPDATE = (
    os.getenv("CACHE_INVALIDATE_ON_KB_UPDATE", "true").lower() == "true"
)

# Logging settings
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Context Management Settings
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "32000"))
