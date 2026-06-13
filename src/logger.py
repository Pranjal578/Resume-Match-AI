import logging
import sys
from logging.handlers import RotatingFileHandler
from src.config import LOG_DIR

# Log file path
LOG_FILE = LOG_DIR / "app.log"

def setup_logger(name: str = "resume_match_ai") -> logging.Logger:
    """Sets up a logger with both console and rotating file handlers."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Format definition
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(filename)s:%(lineno)d] - %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Rotating file handler (up to 10MB per file, keeping 5 backup files)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create a default logger instance
logger = setup_logger()
