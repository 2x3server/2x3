"""
2x3 - Deterministic reconstruction input preparation.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from ..models.project import Project


class InputPreparer:
    """Creates isolated, reproducible input folders for a pipeline run."""

    def __init__(self, project: Project) -> None:
        self.project = project

    def prepare_frame_folder(self) -> Path:
        """Reset the project-owned frame workspace for a video import."""

        self._reset_temporary_directory(self.project.frames_folder)
        return self.project.frames_folder

    def prepare_images(
        self,
        images: list[Path],
    ) -> Path:
        """Stage the current run's validated images in an isolated folder."""

        if not images:
            raise ValueError("No valid images are available for preparation.")

        prepared_folder = self.project.prepared_inputs_folder
        self._reset_temporary_directory(prepared_folder)

        try:
            for index, image_path in enumerate(images):
                source = image_path.resolve()

                if not source.is_file():
                    raise FileNotFoundError(
                        f"Validated image not found: {image_path}"
                    )

                target = prepared_folder / (
                    f"image_{index:06d}{source.suffix.lower()}"
                )

                self._link_or_copy(source, target)

        except Exception:
            self._reset_temporary_directory(prepared_folder)
            raise

        return prepared_folder

    @staticmethod
    def _link_or_copy(source: Path, target: Path) -> None:
        """Use a hard link when possible, otherwise create an independent copy."""

        try:
            os.link(source, target)
        except OSError:
            shutil.copy2(source, target)

    @staticmethod
    def _reset_temporary_directory(directory: Path) -> None:
        """Clear and recreate a pipeline-owned temporary directory."""

        if directory.is_symlink():
            directory.unlink()
        elif directory.exists():
            shutil.rmtree(directory)

        directory.mkdir(parents=True, exist_ok=True)
