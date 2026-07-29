"""
2x3 - Processing pipeline.
"""

from __future__ import annotations

from pathlib import Path

from ..core.configuration_manager import ConfigurationManager
from ..models.project import Project
from .colmap_runner import ColmapRunner
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
        self.project = project
        self.configuration = configuration

    def _run_colmap(self, image_folder: Path) -> None:
        """Execute the first COLMAP reconstruction steps."""

        workspace = self.project.folder / "colmap"

        workspace.mkdir(parents=True, exist_ok=True)

        database = workspace / "database.db"
        sparse = workspace / "sparse"

        sparse.mkdir(parents=True, exist_ok=True)

        runner = ColmapRunner()

        print("\n========================================")
        print("COLMAP Reconstruction")
        print("========================================")

        runner.feature_extractor(
            image_path=image_folder,
            database_path=database,
        )

        runner.exhaustive_matcher(
            database_path=database,
        )

        runner.mapper(
            image_path=image_folder,
            database_path=database,
            output_path=sparse,
        )

        print("\nSparse reconstruction completed.")

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

            image_folder = self.project.frames_folder

        else:

            print("\nMode: IMAGES")

            image_folder = self.project.images_folder

        importer = ImageImporter()
        importer.load(image_folder)

        checker = ImageQualityChecker(self.configuration)
        report = checker.check(importer.images)

        if not report.passed:
            print("Pipeline aborted.")
            return

        print(
            f"\nImage quality passed "
            f"({len(report.valid_images)} valid images)."
        )

        self._run_colmap(image_folder)

        print("\nPipeline completed successfully.")