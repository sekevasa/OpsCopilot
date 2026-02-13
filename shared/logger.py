"""Logging configuration."""

import logging
import json
from typing import Any, Dict
from pythonjsonlogger import jsonlogger
from .config import get_settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


def setup_logging(service_name: str) -> logging.Logger:
    """Setup structured JSON logging."""
    settings = get_settings()

    logger = logging.getLogger(service_name)
    logger.setLevel(settings.log_level)

    # Console handler with JSON formatter
    handler = logging.StreamHandler()
    formatter = CustomJsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
