import contextvars
import logging
import sys

from src.multi_agent_rag.core.config import APP_LOG_FILE, ERROR_LOG_FILE, LOG_LEVEL

# Context variable to store the request ID
request_id_var = contextvars.ContextVar("request_id", default="SYSTEM")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


def setup_logging():
    # Create logger
    logger = logging.getLogger("multi_agent_rag")
    logger.setLevel(LOG_LEVEL)

    # Formatter with request_id
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - [%(request_id)s] - %(levelname)s - %(message)s"
    )

    # Add filter
    rf = RequestIdFilter()
    logger.addFilter(rf)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # App Log File Handler
    try:
        app_handler = logging.FileHandler(APP_LOG_FILE)
        app_handler.setFormatter(formatter)
        logger.addHandler(app_handler)
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not create app log file: {e}")

    # Error Log File Handler
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
