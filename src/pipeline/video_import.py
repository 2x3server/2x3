"""
2x3 - Video import utilities.
"""

from __future__ import annotations

from pathlib import Path

import cv2


class VideoImporter:
    """Loads a video and extracts frames."""

    def __init__(self) -> None:
        self.video_path: Path | None = None

    def load(self, video_path: str | Path) -> bool:
        """Load a video file."""

        self.video_path = Path(video_path)

        if not self.video_path.exists():
            print(f"Video not found: {self.video_path}")
            return False

        print(f"Video loaded: {self.video_path}")
        return True

    def extract_frames(
        self,
        output_folder: str | Path,
        frame_step: int = 30,
    ) -> int:
        """
        Extract one frame every frame_step frames.
        """

        if self.video_path is None:
            print("No video loaded.")
            return 0

        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(self.video_path))

        if not cap.isOpened():
            print(f"Unable to open video: {self.video_path}")
            return 0

        saved = 0
        frame_index = 0

        while True:
            success, frame = cap.read()

            if not success:
                break

            if frame_index % frame_step == 0:
                filename = output_folder / f"frame_{saved:06d}.jpg"
                cv2.imwrite(str(filename), frame)
                saved += 1

            frame_index += 1

        cap.release()

        print(f"Frames extracted: {saved}")
        print(f"Output folder: {output_folder}")

        return saved