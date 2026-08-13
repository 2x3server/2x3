from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

sys.modules.setdefault("cv2", types.SimpleNamespace())
fake_pil_image_module = types.SimpleNamespace(
    Image=object,
    open=lambda *args, **kwargs: None,
)
sys.modules.setdefault(
    "PIL",
    types.SimpleNamespace(Image=fake_pil_image_module),
)
sys.modules.setdefault("PIL.Image", fake_pil_image_module)

from src.pipeline.pipeline import Pipeline
from src.pipeline import pipeline as pipeline_module
from src.pipeline import stl_exporter as stl_exporter_module


class DummyProject:
    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.name = "demo"
        self.video_file = folder / "video.mp4"
        self.images_folder = folder / "images"
        self.frames_folder = folder / "frames"


class DummyConfiguration:
    def __init__(self, folder: Path) -> None:
        self.openmvs_executable_folder = folder


def test_pipeline_fails_fast_on_missing_openmvs_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeOpenMVSRunner:
        def __init__(self, executable_folder: Path) -> None:
            self.executable_folder = executable_folder

        def interface_colmap(
            self,
            input_file: Path,
            output_file: Path,
        ) -> None:
            calls.append("interface_colmap")
            output_file.write_text("scene", encoding="utf-8")

        def densify_point_cloud(self, scene_file: Path) -> None:
            calls.append("densify_point_cloud")
            workspace = scene_file.parent
            (workspace / "scene_dense.mvs").write_text(
                "dense",
                encoding="utf-8",
            )
            (workspace / "scene_dense.ply").write_text(
                "dense-cloud",
                encoding="utf-8",
            )

        def reconstruct_mesh(self, scene_file: Path) -> None:
            calls.append("reconstruct_mesh")
            # Intentionally missing scene_dense_mesh.ply

        def refine_mesh(self, scene_file: Path) -> None:
            calls.append("refine_mesh")

        def texture_mesh(self, scene_file: Path) -> None:
            calls.append("texture_mesh")

    monkeypatch.setattr(
        pipeline_module,
        "OpenMVSRunner",
        FakeOpenMVSRunner,
    )

    project = DummyProject(tmp_path / "project")
    project.folder.mkdir(parents=True, exist_ok=True)

    pipeline = Pipeline(
        project=project,
        configuration=DummyConfiguration(tmp_path),
    )

    with pytest.raises(RuntimeError) as error:
        pipeline._run_openmvs(
            dense_workspace=tmp_path / "colmap" / "dense",
            image_folder=tmp_path / "images",
        )

    message = str(error.value)
    assert "OpenMVS ReconstructMesh" in message
    assert "scene_dense_mesh.ply" in message
    assert calls == [
        "interface_colmap",
        "densify_point_cloud",
        "reconstruct_mesh",
    ]


def test_pipeline_continues_when_all_openmvs_artifacts_exist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeOpenMVSRunner:
        def __init__(self, executable_folder: Path) -> None:
            self.executable_folder = executable_folder

        def interface_colmap(
            self,
            input_file: Path,
            output_file: Path,
        ) -> None:
            output_file.write_text("scene", encoding="utf-8")

        def densify_point_cloud(self, scene_file: Path) -> None:
            workspace = scene_file.parent
            (workspace / "scene_dense.mvs").write_text(
                "dense",
                encoding="utf-8",
            )
            (workspace / "scene_dense.ply").write_text(
                "dense-cloud",
                encoding="utf-8",
            )

        def reconstruct_mesh(self, scene_file: Path) -> None:
            workspace = scene_file.parent
            (workspace / "scene_dense_mesh.ply").write_text(
                "mesh",
                encoding="utf-8",
            )

        def refine_mesh(self, scene_file: Path) -> None:
            workspace = scene_file.parent
            (workspace / "scene_dense_mesh_refine.mvs").write_text(
                "refine-mvs",
                encoding="utf-8",
            )
            (workspace / "scene_dense_mesh_refine.ply").write_text(
                "refine-ply",
                encoding="utf-8",
            )

        def texture_mesh(self, scene_file: Path) -> None:
            workspace = scene_file.parent
            (
                workspace / "scene_dense_mesh_refine_texture.mvs"
            ).write_text("texture-mvs", encoding="utf-8")
            (
                workspace / "scene_dense_mesh_refine_texture.ply"
            ).write_text("texture-ply", encoding="utf-8")

    class FakeSTLExporter:
        def export(self, ply_file: Path, stl_file: Path) -> Path:
            stl_file.parent.mkdir(parents=True, exist_ok=True)
            stl_file.write_bytes(b"stl")
            return stl_file

    monkeypatch.setattr(
        pipeline_module,
        "OpenMVSRunner",
        FakeOpenMVSRunner,
    )
    monkeypatch.setattr(
        stl_exporter_module,
        "STLExporter",
        FakeSTLExporter,
    )

    project = DummyProject(tmp_path / "project")
    project.folder.mkdir(parents=True, exist_ok=True)

    pipeline = Pipeline(
        project=project,
        configuration=DummyConfiguration(tmp_path),
    )

    pipeline._run_openmvs(
        dense_workspace=tmp_path / "colmap" / "dense",
        image_folder=tmp_path / "images",
    )

    assert (
        project.folder
        / "openmvs"
        / "scene_dense_mesh_refine.stl"
    ).exists()
