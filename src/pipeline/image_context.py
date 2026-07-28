"""
2x3 - Shared image context.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL.Image import Image


@dataclass(slots=True)
class ImageContext:
    """
    Shared information about a loaded image.
    """

    path: Path
    image: Image
    width: int
    height: int
    image_format: str | None
    image_mode: str