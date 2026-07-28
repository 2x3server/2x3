"""
2x3 - Image integrity validation.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image


class IntegrityCheck:
    """Checks that image files are readable and not corrupted."""

    def check(self, image_path: Path) -> bool:
        """
        Validate a single image.

        Parameters
        ----------
        image_path:
            Path of the image to validate.

        Returns
        -------
        bool
            True if the image is valid.
        """

        try:
            with Image.open(image_path) as img:
                img.verify()

        except Exception as error:
            print("Status: FAILED")
            print(f"Unreadable image: {image_path}")
            print(f"Reason: {error}")
            return False

        return True