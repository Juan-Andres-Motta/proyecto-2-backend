import logging
import sys
from typing import Any, Dict

from .settings import settings


def get_logging_config(log_level: str) -> Dict[str, Any]:
    """Get logging configuration dictionary."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",  # noqa E501
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": sys.stdout,
                "level": log_level,
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "detailed",
                "filename": "app.log",
                "level": log_level,
            },
        },
        "root": {
            "level": "WARNING",  # Suppress library logs
            "handlers": ["console", "file"],
        },
        "loggers": {
            "src": {  # Only log from our application code
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "WARNING",
                "handlers": [],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "WARNING",
                "handlers": [],
                "propagate": False,
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": [],
                "propagate": False,
            },
        },
    }


def setup_logging():
    """Setup logging configuration."""
    config = get_logging_config(settings.log_level)
    logging.config.dictConfig(config)
