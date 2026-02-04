import logging
import sys
from src.multi_agent_rag.core.config import LOG_LEVEL, APP_LOG_FILE, ERROR_LOG_FILE

def setup_logging():
    # Create logger
    logger = logging.getLogger("multi_agent_rag")
    logger.setLevel(LOG_LEVEL)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # App Log File Handler (All logs)
    try:
        app_handler = logging.FileHandler(APP_LOG_FILE)
        app_handler.setFormatter(formatter)
        logger.addHandler(app_handler)
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not create app log file: {e}")

    # Error Log File Handler (Only Errors/Critical)
    try:
        error_handler = logging.FileHandler(ERROR_LOG_FILE)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not create error log file: {e}")

    return logger

# Singleton-like access
logger = setup_logging()
