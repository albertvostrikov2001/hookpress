"""Logging configuration."""

import logging
import sys

from app.core.log_context import CorrelationIdFilter, JsonFormatter


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(CorrelationIdFilter())
    root.addHandler(handler)
