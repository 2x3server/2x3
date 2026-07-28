"""
2x3 - Image import module.
"""

from __future__ import annotations

from pathlib import Path


class ImageImporter:
    """Loads images from a folder."""

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".tif",
        ".tiff",
        ".bmp",
        ".webp",
    }

    def __init__(self) -> None:
        """Initialize the importer."""

        self.images: list[Path] = []

    def load(self, folder: str) -> None:
        """Load all supported images recursively."""

        print(f"Loading images from: {folder}")

        root = Path(folder).resolve()

        print(f"Searching in: {root}")

        if not root.exists():
            print("ERROR: Folder not found.")
            return

        self.images = sorted(
            file
            for file in root.rglob("*")
            if file.is_file()
            and file.suffix.lower() in self.SUPPORTED_EXTENSIONS
        )

        print()
        print(f"Images found: {len(self.images)}")
        print()

        if not self.images:
            print("No supported image files were found.")
            return

        print("Image list:")

        for image in self.images:
            print(f" - {image}")