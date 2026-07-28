"""
2x3 - Quality report model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class QualityReport:
    """Result of the image quality analysis."""

    valid_images: list[Path] = field(default_factory=list)

    rejected_images: int = 0

    status: str = "FAILED"

    reason: str = ""

    formats: dict[str, int] = field(default_factory=dict)

    modes: dict[str, int] = field(default_factory=dict)

    minimum_resolution: tuple[int, int] | None = None

    maximum_resolution: tuple[int, int] | None = None

    @property
    def passed(self) -> bool:
        """Return True if the dataset passed the checks."""

        return self.status == "PASSED"