"""
2x3 - Project model.
"""

from __future__ import annotations

from pathlib import Path


class Project:
    """Represents an opened 2x3 project."""

    def __init__(self, project_folder: Path) -> None:
        """Initialize the project."""

        self.folder = project_folder
        self.name = project_folder.name

        self.video_file = self.folder / "video.mp4"

        self.images_folder = self.folder / "images"
        self.frames_folder = self.folder / "frames"
        self.metadata_folder = self.folder / "metadata"
        self.output_folder = self.folder / "output"

        self.cache_folder = self.folder / "cache"
        self.masks_folder = self.folder / "masks"
        self.sparse_folder = self.folder / "sparse"
        self.dense_folder = self.folder / "dense"
        self.mesh_folder = self.folder / "mesh"
        self.texture_folder = self.folder / "texture"
        self.logs_folder = self.folder / "logs"

    def create_structure(self) -> None:
        """Create the project folder structure if it does not exist."""

        self.folder.mkdir(parents=True, exist_ok=True)

        folders = (
            self.images_folder,
            self.frames_folder,
            self.metadata_folder,
            self.output_folder,
            self.cache_folder,
            self.masks_folder,
            self.sparse_folder,
            self.dense_folder,
            self.mesh_folder,
            self.texture_folder,
            self.logs_folder,
        )

        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)