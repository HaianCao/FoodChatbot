"""
Logging configuration utilities for FoodChatbot crawler scripts.

Provides setup_logging to configure process-safe console logging.
File logging is disabled to avoid file lock issues in multiprocessing.

Author: FoodChatbot Team
"""

import logging
import os
from pathlib import Path

LOG_DIR: str = "logs"
LOG_FILE_NAME: str = "crawl_parallel.log"
LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB per file
LOG_BACKUP_COUNT: int = 5  # Number of backup files to keep

def setup_logging() -> None:
    """
    Configure logging to output to console only (process-safe).

    Call this at the start of each crawler script to ensure logs are sent to the console.
    File logging is not used to avoid deadlocks or write errors in multiprocessing.

    Example:
        >>> from packages.logging_handler import setup_logging
        >>> setup_logging()
        >>> logging.info("Crawler started!")
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
