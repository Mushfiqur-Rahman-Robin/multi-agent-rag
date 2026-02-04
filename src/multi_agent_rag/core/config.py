import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Models
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash")
SEARCH_MODEL = os.getenv("SEARCH_MODEL", "gemini-2.0-flash")
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "gemini-2.0-flash")
CODER_MODEL = os.getenv("CODER_MODEL", "gemini-2.0-flash")

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db:5432/rag_db")
DB_MAX_RETRIES = int(os.getenv("DB_MAX_RETRIES", "5"))
DB_RETRY_DELAY = int(os.getenv("DB_RETRY_DELAY", "5"))

# Logging settings
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API settings
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
