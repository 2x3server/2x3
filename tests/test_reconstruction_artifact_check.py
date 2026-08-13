from pathlib import Path

import pytest

from src.pipeline.checks.reconstruction_artifacts import (
    ReconstructionArtifactCheck,
)


def test_require_files_passes_when_all_exist(tmp_path: Path) -> None:
    artifact = tmp_path / "scene.mvs"
    artifact.write_text("ok", encoding="utf-8")

    check = ReconstructionArtifactCheck()

    check.require_files(
        stage="OpenMVS InterfaceCOLMAP",
        files=[artifact],
    )


def test_require_files_raises_with_stage_and_missing_paths(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "scene_dense.ply"

    check = ReconstructionArtifactCheck()

    with pytest.raises(RuntimeError) as error:
        check.require_files(
            stage="OpenMVS DensifyPointCloud",
            files=[missing],
        )

    message = str(error.value)
    assert "OpenMVS DensifyPointCloud" in message
    assert str(missing) in message


def test_require_non_empty_directory_raises_for_empty_directory(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "images"
    directory.mkdir()

    check = ReconstructionArtifactCheck()

    with pytest.raises(RuntimeError) as error:
        check.require_non_empty_directory(
            stage="COLMAP image_undistorter",
            directory=directory,
        )

    message = str(error.value)
    assert "COLMAP image_undistorter" in message
    assert str(directory) in message
