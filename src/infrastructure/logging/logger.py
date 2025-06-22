import logging
import sys
from typing import Optional
from logging import Logger

class CleanFormatter(logging.Formatter):
    """Clean, streamlined formatter for album cleaner logs."""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Use colors if terminal supports it
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Clean format with minimal timestamp
        timestamp = self.formatTime(record, '%H:%M:%S')
        
        # Different formats for different log levels
        if record.levelname == 'INFO':
            # For INFO, just show the message with minimal formatting
            return f"{color}[{timestamp}]{reset} {record.getMessage()}"
        elif record.levelname in ['WARNING', 'ERROR', 'CRITICAL']:
            # For errors/warnings, include level
            return f"{color}[{timestamp}] {record.levelname}{reset} {record.getMessage()}"
        else:
            # For DEBUG, include more context
            return f"{color}[{timestamp}] {record.levelname}{reset} {record.name} - {record.getMessage()}"

def get_logger(name: Optional[str] = None, level: str = "INFO") -> Logger:
    """Get configured logger instance with streamlined output."""
    logger_name = name or "album_cleaner"
    logger = logging.getLogger(logger_name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Set log level
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Use clean formatter
        formatter = CleanFormatter()
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        logger.propagate = False
    
    return logger

# Create the main logger instance
logger = get_logger()
