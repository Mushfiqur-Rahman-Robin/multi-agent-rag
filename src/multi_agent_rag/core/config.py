import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# API Keys (Required for agents)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Application Settings
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_RELOAD = os.getenv("APP_RELOAD", "true").lower() == "true"

# Models
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4.1-mini")
SEARCH_MODEL = os.getenv("SEARCH_MODEL", "gpt-4.1-mini")
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "gpt-4.1-mini")
CODER_MODEL = os.getenv("CODER_MODEL", "gpt-4.1-mini")

# Database settings
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "rag_db")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")

# Construct DATABASE_URL if not explicitly provided
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

DB_MAX_RETRIES = int(os.getenv("DB_MAX_RETRIES", "5"))
DB_RETRY_DELAY = int(os.getenv("DB_RETRY_DELAY", "5"))

# Logging settings
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Storage settings
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
