"""
2x3 - Processing pipeline.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from threading import Event
from typing import Callable

from ..core.configuration_manager import ConfigurationManager
from ..models.pipeline_event import PipelineEvent, PipelineState
from ..models.project import Project
from .colmap_runner import ColmapRunner
from .checks.reconstruction_artifacts import ReconstructionArtifactCheck
from .image_quality import ImageQualityChecker
from .import_images import ImageImporter
from .input_preparation import InputPreparer
from .openmvs_runner import OpenMVSRunner
from .video_import import VideoImporter


class Pipeline:
    """Coordinates the processing pipeline."""

    def __init__(
        self,
        project: Project,
        configuration: ConfigurationManager,
        event_listener: Callable[[PipelineEvent], None] | None = None,
    ) -> None:
        self.project = project
        self.configuration = configuration
        self._event_listeners: list[Callable[[PipelineEvent], None]] = []
        self._progress = 0.0
        self._cancellation_requested = Event()

        if event_listener is not None:
            self.add_event_listener(event_listener)

    def add_event_listener(
        self,
        listener: Callable[[PipelineEvent], None],
    ) -> None:
        """Register a callback for pipeline progress events."""

        self._event_listeners.append(listener)

    def cancel(self) -> None:
        """Request cancellation at the next pipeline stage boundary."""

        self._cancellation_requested.set()

    def _check_cancellation(self) -> None:
        """Stop execution when cancellation has been requested."""

        if self._cancellation_requested.is_set():
            raise PipelineCancelled()

    def _emit(
        self,
        state: PipelineState,
        message: str,
        progress: float,
        error: str | None = None,
    ) -> None:
        """Publish a progress event without coupling to a presentation layer."""

        self._progress = progress
        event = PipelineEvent(
            state=state,
            message=message,
            progress=progress,
            error=error,
        )

        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception:
                logging.getLogger(__name__).exception(
                    "Pipeline event listener failed."
                )

    def _abort(self, reason: str) -> None:
        """Report a non-recoverable pipeline condition."""

        self._emit(
            PipelineState.FAILED,
            "Pipeline aborted.",
            self._progress,
            error=reason,
        )
        print("Pipeline aborted.")

    def _cancelled(self) -> None:
        """Report a cooperative pipeline cancellation."""

        self._emit(
            PipelineState.CANCELLED,
            "Pipeline cancelled.",
            self._progress,
        )
        print("Pipeline cancelled.")

    def _reset_colmap_workspace(self) -> Path:
        """Create an empty COLMAP workspace for the current execution."""

        workspace = self.project.folder / "colmap"

        if workspace.is_symlink():
            workspace.unlink()
        elif workspace.exists():
            shutil.rmtree(workspace)

        workspace.mkdir(parents=True, exist_ok=True)

        return workspace

    def _run_colmap(self, image_folder: Path) -> Path:
        """Execute the COLMAP reconstruction pipeline."""

        self._check_cancellation()

        workspace = self._reset_colmap_workspace()

        database = workspace / "database.db"
        sparse = workspace / "sparse"
        dense = workspace / "dense"

        sparse.mkdir(parents=True, exist_ok=True)
        dense.mkdir(parents=True, exist_ok=True)

        runner = ColmapRunner()
        artifact_check = ReconstructionArtifactCheck()

        print("\n========================================")
        print("COLMAP Reconstruction")
        print("========================================")

        self._emit(
            PipelineState.RUNNING_COLMAP,
            "Extracting COLMAP features.",
            35.0,
        )
        runner.feature_extractor(
            image_path=image_folder,
            database_path=database,
        )
        self._check_cancellation()

        self._emit(
            PipelineState.RUNNING_COLMAP,
            "Matching COLMAP image features.",
            45.0,
        )
        runner.exhaustive_matcher(
            database_path=database,
        )
        self._check_cancellation()

        self._emit(
            PipelineState.RUNNING_COLMAP,
            "Building the sparse COLMAP reconstruction.",
            55.0,
        )
        runner.mapper(
            image_path=image_folder,
            database_path=database,
            output_path=sparse,
        )
        self._check_cancellation()
        artifact_check.check_sparse_model(sparse / "0")

        print("\nSparse reconstruction completed.")

        self._emit(
            PipelineState.RUNNING_COLMAP,
            "Undistorting images for dense reconstruction.",
            65.0,
        )
        runner.image_undistorter(
            image_path=image_folder,
            input_path=sparse / "0",
            output_path=dense,
        )
        self._check_cancellation()
        artifact_check.check_undistorted_workspace(dense)

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

        self._check_cancellation()

        workspace = self.project.folder / "openmvs"
        workspace.mkdir(parents=True, exist_ok=True)

        runner = OpenMVSRunner(
            self.configuration.openmvs_executable_folder,
        )
        artifact_check = ReconstructionArtifactCheck()

        scene = workspace / "scene.mvs"

        self._emit(
            PipelineState.RUNNING_OPENMVS,
            "Importing the COLMAP reconstruction into OpenMVS.",
            72.0,
        )
        runner.interface_colmap(
            input_file=dense_workspace,
            output_file=scene,
        )
        self._check_cancellation()
        artifact_check.check_openmvs_scene(scene)

        self._emit(
            PipelineState.RUNNING_OPENMVS,
            "Densifying the OpenMVS point cloud.",
            80.0,
        )
        runner.densify_point_cloud(scene)
        self._check_cancellation()

        scene = workspace / "scene_dense.mvs"
        artifact_check.check_dense_point_cloud(scene)

        self._emit(
            PipelineState.RUNNING_OPENMVS,
            "Reconstructing the mesh.",
            87.0,
        )
        runner.reconstruct_mesh(scene)
        self._check_cancellation()
        artifact_check.check_mesh(scene)

        self._emit(
            PipelineState.RUNNING_OPENMVS,
            "Refining the mesh.",
            93.0,
        )
        runner.refine_mesh(scene)
        self._check_cancellation()
        artifact_check.check_refined_mesh(scene)

        self._emit(
            PipelineState.RUNNING_OPENMVS,
            "Texturing the mesh.",
            98.0,
        )
        runner.texture_mesh(scene)
        self._check_cancellation()
        artifact_check.check_textured_mesh(scene)

        print("\nOpenMVS reconstruction completed.")

    def run(self) -> None:
        """Execute the processing pipeline."""

        self._progress = 0.0
        self._cancellation_requested.clear()

        print("Pipeline started.")
        print(f"Project: {self.project.name}")

        try:
            self._emit(
                PipelineState.IDLE,
                "Pipeline is ready to start.",
                0.0,
            )
            self._emit(
                PipelineState.PREPARING_INPUT,
                "Preparing reconstruction input.",
                5.0,
            )

            self._check_cancellation()

            preparer = InputPreparer(self.project)

            if self.project.video_file.exists():

                print("\nMode: VIDEO")

                video = VideoImporter()

                if not video.load(self.project.video_file):
                    self._abort("Unable to load the project video.")
                    return

                self._emit(
                    PipelineState.PREPARING_INPUT,
                    "Resetting the video frame workspace.",
                    10.0,
                )
                frame_folder = preparer.prepare_frame_folder()
                self._check_cancellation()

                self._emit(
                    PipelineState.PREPARING_INPUT,
                    "Extracting video frames.",
                    15.0,
                )
                frame_count = video.extract_frames(
                    output_folder=frame_folder,
                    frame_step=self.configuration.frame_step,
                )
                self._check_cancellation()

                if frame_count == 0:
                    self._abort("No frames could be extracted from the video.")
                    return

                image_folder = frame_folder

            else:

                print("\nMode: IMAGES")

                image_folder = self.project.images_folder

            self._emit(
                PipelineState.VALIDATING_IMAGES,
                "Loading input images.",
                20.0,
            )
            importer = ImageImporter()
            importer.load(image_folder)
            self._check_cancellation()

            self._emit(
                PipelineState.VALIDATING_IMAGES,
                "Checking image quality.",
                25.0,
            )
            checker = ImageQualityChecker(self.configuration)
            report = checker.check(importer.images)
            self._check_cancellation()

            if not report.passed:
                self._abort(report.reason)
                return

            print(
                f"\nImage quality passed "
                f"({len(report.valid_images)} valid images)."
            )

            self._emit(
                PipelineState.PREPARING_INPUT,
                "Preparing validated images for reconstruction.",
                30.0,
            )
            reconstruction_images = preparer.prepare_images(
                report.valid_images,
            )
            self._check_cancellation()

            dense_workspace = self._run_colmap(reconstruction_images)

            self._run_openmvs(
                dense_workspace=dense_workspace,
                image_folder=reconstruction_images,
            )

            self._emit(
                PipelineState.COMPLETED,
                "Pipeline completed successfully.",
                100.0,
            )
            print("\nPipeline completed successfully.")

        except PipelineCancelled:
            self._cancelled()

        except Exception as error:
            self._emit(
                PipelineState.FAILED,
                "Pipeline failed.",
                self._progress,
                error=str(error),
            )
            raise


class PipelineCancelled(Exception):
    """Internal signal used for cooperative pipeline cancellation."""
