"""
2x3 - Logging configuration.
"""

from __future__ import annotations

import logging

from . import settings


def configure_logger() -> None:
    """Configure the application logger."""

    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(levelname)s - %(message)s",
    )