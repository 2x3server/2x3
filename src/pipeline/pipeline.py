"""
2x3 - Processing pipeline.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from ..core.configuration_manager import ConfigurationManager
from ..models.project import Project
from .colmap_runner import ColmapRunner
from .image_quality import ImageQualityChecker
from .import_images import ImageImporter
from .openmvs_runner import OpenMVSRunner
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

    def _run_colmap(self, image_folder: Path) -> Path:
        """Execute the COLMAP reconstruction pipeline."""

        workspace = self.project.folder / "colmap"

        workspace.mkdir(parents=True, exist_ok=True)

        database = workspace / "database.db"
        sparse = workspace / "sparse"
        dense = workspace / "dense"

        if database.exists():
            database.unlink()

        if sparse.exists():
            shutil.rmtree(sparse)

        if dense.exists():
            shutil.rmtree(dense)

        sparse.mkdir(parents=True, exist_ok=True)
        dense.mkdir(parents=True, exist_ok=True)

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

        runner.image_undistorter(
            image_path=image_folder,
            input_path=sparse / "0",
            output_path=dense,
        )

        print("\nImage undistortion completed.")

        #         runner.patch_match_stereo(
        #             workspace_path=dense,
        #         )

        print("\nPatch Match Stereo completed.")

        return dense

    def _run_openmvs(
        self,
        dense_workspace: Path,
        image_folder: Path,
    ) -> None:
        """Execute the OpenMVS reconstruction pipeline."""

        workspace = self.project.folder / "openmvs"
        workspace.mkdir(parents=True, exist_ok=True)

        runner = OpenMVSRunner(
            self.configuration.openmvs_executable_folder,
        )

        scene = workspace / "scene.mvs"

        runner.interface_colmap(
            input_file=dense_workspace,
            output_file=scene,
        )

        runner.densify_point_cloud(scene)

        scene = workspace / "scene_dense.mvs"

        runner.reconstruct_mesh(scene)
        runner.refine_mesh(scene)
        runner.texture_mesh(scene)

        from .stl_exporter import STLExporter

        mesh_file = workspace / "scene_dense_mesh_refine.ply"
        stl_file = workspace / "scene_dense_mesh_refine.stl"

        STLExporter().export(
            ply_file=mesh_file,
            stl_file=stl_file,
        )

        print("\nOpenMVS reconstruction completed.")

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

        dense_workspace = self._run_colmap(image_folder)

        self._run_openmvs(
            dense_workspace=dense_workspace,
            image_folder=image_folder,
        )

        print("\nPipeline completed successfully.")