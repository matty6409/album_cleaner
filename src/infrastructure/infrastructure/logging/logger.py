import logging
import sys
import json
from logging import Logger

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'level': record.levelname,
            'time': self.formatTime(record, self.datefmt),
            'name': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

# Singleton logger instance
logger: Logger = logging.getLogger("album_cleaner")
logger.setLevel(logging.DEBUG)

# Console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(JsonFormatter())

# File handler
fh = logging.FileHandler("album_cleaner.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(JsonFormatter())

# Avoid duplicate handlers
if not logger.hasHandlers():
    logger.addHandler(ch)
    logger.addHandler(fh)

logger.propagate = False 