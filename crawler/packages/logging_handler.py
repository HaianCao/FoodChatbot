import logging
import os
from pathlib import Path

LOG_DIR: str = "logs"
LOG_FILE_NAME: str = "crawl_parallel.log"
LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB per file
LOG_BACKUP_COUNT: int = 5  # Number of backup files to keep

def setup_logging() -> None:
    """Configure logging to console only (process-safe).
    
    Note: File logging is disabled for multiprocessing to avoid file lock issues.
    Each process logs to console, which is thread-safe.
    """
    # Only log to console - this is process-safe
    # Avoid RotatingFileHandler in multiprocessing context
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(threadName)s] %(message)s")
    )
    console_handler.setLevel(logging.INFO)
    
    # Only add console handler if not already configured
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.DEBUG)
