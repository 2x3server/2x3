"""
2x3 - Pipeline progress event model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class PipelineState(str, Enum):
    """Execution states emitted by the reconstruction pipeline."""

    IDLE = "IDLE"
    PREPARING_INPUT = "PREPARING_INPUT"
    VALIDATING_IMAGES = "VALIDATING_IMAGES"
    RUNNING_COLMAP = "RUNNING_COLMAP"
    RUNNING_OPENMVS = "RUNNING_OPENMVS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class PipelineEvent:
    """An immutable progress update published by the pipeline."""

    state: PipelineState
    message: str
    progress: float
    error: str | None = None
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """Ensure progress is expressed as a percentage."""

        if not 0.0 <= self.progress <= 100.0:
            raise ValueError("Pipeline event progress must be between 0 and 100.")
