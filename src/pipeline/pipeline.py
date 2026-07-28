"""
2x3 - Processing pipeline.
"""

from __future__ import annotations

from ..core.configuration_manager import ConfigurationManager
from ..models.project import Project
from .image_quality import ImageQualityChecker
from .import_images import ImageImporter
from .video_import import VideoImporter


class Pipeline:
    """Coordinates the processing pipeline."""

    def __init__(
        self,
        project: Project,
        configuration: ConfigurationManager,
    ) -> None:
        """Initialize the pipeline."""

        self.project = project
        self.configuration = configuration

    def run(self) -> None:
        """Execute the processing pipeline."""

        print("Pipeline started.")
        print(f"Project: {self.project.name}")

        if self.project.video_file.exists():
            print("\nMode: VIDEO")

            video = VideoImporter()

            if not video.load(self.project.video_file):
                print("Pipeline aborted.")
                return

            frame_count = video.extract_frames(
                output_folder=self.project.frames_folder,
                frame_step=self.configuration.frame_step,
            )

            if frame_count == 0:
                print("Pipeline aborted.")
                return

            importer = ImageImporter()
            importer.load(self.project.frames_folder)

            checker = ImageQualityChecker(self.configuration)
            report = checker.check(importer.images)

            if not report.passed:
                print("Pipeline aborted.")
                return

            print(
                f"Pipeline completed successfully "
                f"({len(report.valid_images)} valid images)."
            )
            return

        print("\nMode: IMAGES")

        importer = ImageImporter()
        importer.load(self.project.images_folder)

        checker = ImageQualityChecker(self.configuration)
        report = checker.check(importer.images)

        if not report.passed:
            print("Pipeline aborted.")
            return

        print(
            f"Pipeline completed successfully "
            f"({len(report.valid_images)} valid images)."
        )