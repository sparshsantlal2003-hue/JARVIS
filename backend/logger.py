import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from backend.config import settings

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

is_background = '--background' in sys.argv

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(settings.log_level.upper())
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        if is_background:
            # Main log file
            file_handler = RotatingFileHandler(os.path.join(log_dir, 'jarvis.log'), maxBytes=5*1024*1024, backupCount=3)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Error log file (WARNING and above)
            error_handler = RotatingFileHandler(os.path.join(log_dir, 'errors.log'), maxBytes=5*1024*1024, backupCount=3)
            error_handler.setLevel(logging.WARNING)
            error_handler.setFormatter(formatter)
            logger.addHandler(error_handler)
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
    return logger
