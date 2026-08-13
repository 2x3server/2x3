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
            (workspace / "scene_dense_mesh.mvs").write_text(
                "mesh-mvs",
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


def test_scene_path_updated_after_reconstruct_mesh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RefineMesh must receive scene_dense_mesh.mvs, TextureMesh must
    receive scene_dense_mesh_refine.mvs."""

    received: dict[str, Path] = {}

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
            (workspace / "scene_dense_mesh.mvs").write_text(
                "mesh-mvs",
                encoding="utf-8",
            )

        def refine_mesh(self, scene_file: Path) -> None:
            received["refine_mesh"] = scene_file
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
            received["texture_mesh"] = scene_file
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

    openmvs = project.folder / "openmvs"
    assert received["refine_mesh"] == openmvs / "scene_dense_mesh.mvs"
    assert received["texture_mesh"] == openmvs / "scene_dense_mesh_refine.mvs"


# ---------------------------------------------------------------------------
# COLMAP workspace isolation tests
# ---------------------------------------------------------------------------


def _make_fake_colmap_runner(calls: list[str]) -> type:
    """Return a FakeColmapRunner that records calls and creates minimal
    artifacts so artifact checks pass."""

    class FakeColmapRunner:
        def __init__(self) -> None:
            pass

        def feature_extractor(
            self,
            image_path: Path,
            database_path: Path,
        ) -> None:
            calls.append("feature_extractor")
            database_path.write_bytes(b"db")

        def exhaustive_matcher(self, database_path: Path) -> None:
            calls.append("exhaustive_matcher")

        def mapper(
            self,
            image_path: Path,
            database_path: Path,
            output_path: Path,
        ) -> None:
            calls.append("mapper")
            sparse_model = output_path / "0"
            sparse_model.mkdir(parents=True, exist_ok=True)
            for name in ("cameras.bin", "images.bin", "points3D.bin"):
                (sparse_model / name).write_bytes(b"bin")

        def image_undistorter(
            self,
            image_path: Path,
            input_path: Path,
            output_path: Path,
        ) -> None:
            calls.append("image_undistorter")
            dense_sparse = output_path / "sparse"
            dense_sparse.mkdir(parents=True, exist_ok=True)
            for name in ("cameras.bin", "images.bin", "points3D.bin"):
                (dense_sparse / name).write_bytes(b"bin")
            dense_images = output_path / "images"
            dense_images.mkdir(parents=True, exist_ok=True)
            (dense_images / "img.jpg").write_bytes(b"img")

    return FakeColmapRunner


def test_colmap_workspace_is_removed_before_new_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An existing colmap workspace (with stale database.db) must be
    deleted before a new COLMAP run starts."""

    calls: list[str] = []

    monkeypatch.setattr(
        pipeline_module,
        "ColmapRunner",
        _make_fake_colmap_runner(calls),
    )

    project = DummyProject(tmp_path / "project")
    project.folder.mkdir(parents=True, exist_ok=True)

    # Plant a stale workspace with an existing database.
    stale_workspace = project.folder / "colmap"
    stale_workspace.mkdir(parents=True)
    stale_db = stale_workspace / "database.db"
    stale_db.write_bytes(b"stale")
    stale_extra = stale_workspace / "sparse" / "old_model"
    stale_extra.mkdir(parents=True)
    (stale_extra / "cameras.bin").write_bytes(b"old")

    pipeline = Pipeline(
        project=project,
        configuration=DummyConfiguration(tmp_path),
    )

    # _run_colmap should succeed and produce a fresh workspace.
    pipeline._run_colmap(image_folder=tmp_path / "images")

    # The database written by FakeColmapRunner must be freshly created —
    # confirming the stale one was wiped.
    fresh_db = project.folder / "colmap" / "database.db"
    assert fresh_db.exists()
    assert fresh_db.read_bytes() == b"db"

    # The old sparse sub-model must no longer exist.
    assert not stale_extra.exists()


def test_colmap_workspace_recreated_cleanly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After cleanup the COLMAP workspace must be recreated as an empty
    directory before any COLMAP tool is invoked."""

    created_before_first_call: list[bool] = []
    calls: list[str] = []

    class FakeColmapRunnerProbe:
        def __init__(self) -> None:
            pass

        def feature_extractor(
            self,
            image_path: Path,
            database_path: Path,
        ) -> None:
            calls.append("feature_extractor")
            # Workspace must already exist at this point.
            created_before_first_call.append(
                database_path.parent.exists()
            )
            database_path.write_bytes(b"db")

        def exhaustive_matcher(self, database_path: Path) -> None:
            calls.append("exhaustive_matcher")

        def mapper(
            self,
            image_path: Path,
            database_path: Path,
            output_path: Path,
        ) -> None:
            calls.append("mapper")
            sparse_model = output_path / "0"
            sparse_model.mkdir(parents=True, exist_ok=True)
            for name in ("cameras.bin", "images.bin", "points3D.bin"):
                (sparse_model / name).write_bytes(b"bin")

        def image_undistorter(
            self,
            image_path: Path,
            input_path: Path,
            output_path: Path,
        ) -> None:
            calls.append("image_undistorter")
            dense_sparse = output_path / "sparse"
            dense_sparse.mkdir(parents=True, exist_ok=True)
            for name in ("cameras.bin", "images.bin", "points3D.bin"):
                (dense_sparse / name).write_bytes(b"bin")
            dense_images = output_path / "images"
            dense_images.mkdir(parents=True, exist_ok=True)
            (dense_images / "img.jpg").write_bytes(b"img")

    monkeypatch.setattr(
        pipeline_module,
        "ColmapRunner",
        FakeColmapRunnerProbe,
    )

    project = DummyProject(tmp_path / "project")
    project.folder.mkdir(parents=True, exist_ok=True)

    pipeline = Pipeline(
        project=project,
        configuration=DummyConfiguration(tmp_path),
    )

    pipeline._run_colmap(image_folder=tmp_path / "images")

    assert created_before_first_call == [True]


def test_colmap_cleanup_does_not_touch_unrelated_folders(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cleanup must never delete project images, frames, video, or
    openmvs folders."""

    calls: list[str] = []

    monkeypatch.setattr(
        pipeline_module,
        "ColmapRunner",
        _make_fake_colmap_runner(calls),
    )

    project = DummyProject(tmp_path / "project")
    project.folder.mkdir(parents=True, exist_ok=True)

    # Create unrelated project data that must survive.
    sentinel_files = {
        "images": project.folder / "images" / "photo.jpg",
        "frames": project.folder / "frames" / "frame_000000.jpg",
        "video": project.folder / "video.mp4",
        "openmvs": project.folder / "openmvs" / "scene.mvs",
    }
    for path in sentinel_files.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"sentinel")

    pipeline = Pipeline(
        project=project,
        configuration=DummyConfiguration(tmp_path),
    )

    pipeline._run_colmap(image_folder=tmp_path / "images")

    for name, path in sentinel_files.items():
        assert path.exists(), f"Sentinel file was deleted: {name}"
