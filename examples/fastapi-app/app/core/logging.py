"""Structured logging configuration using structlog."""

import logging
import structlog


def configure_logging(log_level: str = "INFO", json_output: bool = False) -> None:
    """Configure structlog. Call once at startup."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if json_output else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level.upper())),
    )
