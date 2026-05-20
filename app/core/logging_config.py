"""Logging configuration for the AI service."""

import logging


def setup_logging(level: str = "INFO") -> None:
    """Configure basic application logging."""

    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
