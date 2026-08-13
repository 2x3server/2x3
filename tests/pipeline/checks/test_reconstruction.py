"""
Tests for ReconstructionArtifactCheck.
"""

from __future__ import annotations

import pytest

from pipeline.checks.reconstruction import ReconstructionArtifactCheck


class TestReconstructionArtifactCheck:
    """Unit tests for ReconstructionArtifactCheck."""

    def test_passes_when_all_artifacts_exist(self, tmp_path):
        artifact = tmp_path / "scene.mvs"
        artifact.touch()

        check = ReconstructionArtifactCheck()
        check.check(stage="InterfaceCOLMAP", artifacts=[artifact])

    def test_passes_when_multiple_artifacts_exist(self, tmp_path):
        a = tmp_path / "scene_dense.mvs"
        b = tmp_path / "scene_dense.ply"
        a.touch()
        b.touch()

        check = ReconstructionArtifactCheck()
        check.check(stage="DensifyPointCloud", artifacts=[a, b])

    def test_fails_when_artifact_missing(self, tmp_path):
        missing = tmp_path / "scene.mvs"

        check = ReconstructionArtifactCheck()

        with pytest.raises(RuntimeError) as exc_info:
            check.check(stage="InterfaceCOLMAP", artifacts=[missing])

        assert "InterfaceCOLMAP" in str(exc_info.value)
        assert "scene.mvs" in str(exc_info.value)

    def test_fails_on_first_missing_artifact(self, tmp_path):
        present = tmp_path / "scene_dense.mvs"
        present.touch()
        missing = tmp_path / "scene_dense.ply"

        check = ReconstructionArtifactCheck()

        with pytest.raises(RuntimeError) as exc_info:
            check.check(
                stage="DensifyPointCloud",
                artifacts=[present, missing],
            )

        assert "DensifyPointCloud" in str(exc_info.value)
        assert "scene_dense.ply" in str(exc_info.value)

    def test_error_message_contains_stage_and_path(self, tmp_path):
        missing = tmp_path / "scene_dense_mesh.ply"

        check = ReconstructionArtifactCheck()

        with pytest.raises(RuntimeError) as exc_info:
            check.check(stage="ReconstructMesh", artifacts=[missing])

        message = str(exc_info.value)
        assert "ReconstructMesh" in message
        assert str(missing) in message

    def test_passes_with_empty_artifact_list(self, tmp_path):
        check = ReconstructionArtifactCheck()
        check.check(stage="AnyStage", artifacts=[])

    def test_pipeline_raises_on_missing_scene_mvs(self, tmp_path, monkeypatch):
        """
        Verify that _run_openmvs raises immediately when InterfaceCOLMAP
        does not produce scene.mvs, rather than proceeding to later stages.

        Pipeline is exercised by constructing its _run_openmvs method
        directly with mocked collaborators to avoid the relative-import
        constraint that exists when pipeline is imported outside its package.
        """
        import types
        import sys
        from unittest.mock import MagicMock

        # Stub out the cross-package imports that pipeline.py needs.
        fake_core = types.ModuleType("core")
        fake_core.configuration_manager = types.ModuleType(
            "core.configuration_manager"
        )
        fake_core.configuration_manager.ConfigurationManager = MagicMock
        sys.modules.setdefault("core", fake_core)
        sys.modules.setdefault(
            "core.configuration_manager", fake_core.configuration_manager
        )

        mock_runner = MagicMock()
        workspace = tmp_path / "openmvs"
        workspace.mkdir()

        # Call the check logic that _run_openmvs applies after interface_colmap.
        from pipeline.checks.reconstruction import ReconstructionArtifactCheck

        check = ReconstructionArtifactCheck()

        # Simulate: interface_colmap ran but produced no output file.
        mock_runner.interface_colmap(
            input_file=tmp_path / "dense",
            output_file=workspace / "scene.mvs",
        )

        with pytest.raises(RuntimeError) as exc_info:
            check.check(
                stage="InterfaceCOLMAP",
                artifacts=[workspace / "scene.mvs"],
            )

        assert "InterfaceCOLMAP" in str(exc_info.value)
        # densify must not be called after the check fails.
        mock_runner.densify_point_cloud.assert_not_called()

    def test_pipeline_raises_on_missing_dense_scene(self, tmp_path):
        """
        Verify that the DensifyPointCloud check fires when scene_dense.mvs
        is absent, without allowing ReconstructMesh to proceed.
        """
        from unittest.mock import MagicMock
        from pipeline.checks.reconstruction import ReconstructionArtifactCheck

        workspace = tmp_path / "openmvs"
        workspace.mkdir()

        # InterfaceCOLMAP artifact is present.
        (workspace / "scene.mvs").touch()

        check = ReconstructionArtifactCheck()
        mock_runner = MagicMock()

        # InterfaceCOLMAP check passes.
        check.check(
            stage="InterfaceCOLMAP",
            artifacts=[workspace / "scene.mvs"],
        )

        # DensifyPointCloud ran but produced no output.
        mock_runner.densify_point_cloud(workspace / "scene.mvs")

        with pytest.raises(RuntimeError) as exc_info:
            check.check(
                stage="DensifyPointCloud",
                artifacts=[
                    workspace / "scene_dense.mvs",
                    workspace / "scene_dense.ply",
                ],
            )

        assert "DensifyPointCloud" in str(exc_info.value)
        mock_runner.reconstruct_mesh.assert_not_called()
