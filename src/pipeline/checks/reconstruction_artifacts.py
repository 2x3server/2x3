"""
2x3 - Reconstruction artifact validation.
"""

from __future__ import annotations

from pathlib import Path


class ReconstructionArtifactCheck:
    """Validates mandatory outputs produced by reconstruction stages."""

    @staticmethod
    def _require_file(path: Path, artifact_name: str) -> None:
        if not path.is_file():
            raise RuntimeError(
                f"Missing required artifact: {artifact_name} ({path})"
            )

    @staticmethod
    def _require_non_empty_directory(
        path: Path,
        artifact_name: str,
    ) -> None:
        if not path.is_dir() or not any(path.iterdir()):
            raise RuntimeError(
                f"Missing required artifact: {artifact_name} ({path})"
            )

    def check_sparse_model(self, sparse_model: Path) -> None:
        """Validate the binary COLMAP sparse model used for undistortion."""

        self._require_file(sparse_model / "cameras.bin", "COLMAP cameras")
        self._require_file(sparse_model / "images.bin", "COLMAP images")
        self._require_file(sparse_model / "points3D.bin", "COLMAP 3D points")

    def check_undistorted_workspace(self, workspace: Path) -> None:
        """Validate the COLMAP workspace required by OpenMVS."""

        self._require_non_empty_directory(
            workspace / "images",
            "undistorted COLMAP images",
        )
        self.check_sparse_model(workspace / "sparse")

    def check_openmvs_scene(self, scene: Path) -> None:
        """Validate the OpenMVS scene generated from COLMAP."""

        self._require_file(scene, "OpenMVS scene")

    def check_dense_point_cloud(self, scene: Path) -> None:
        """Validate the dense OpenMVS scene and point cloud."""

        self._require_file(scene, "OpenMVS dense scene")
        self._require_file(
            scene.with_suffix(".ply"),
            "OpenMVS dense point cloud",
        )

    def check_mesh(self, scene: Path) -> None:
        """Validate the mesh required by the refinement stage."""

        self._require_file(
            scene.with_name(scene.stem + "_mesh.ply"),
            "OpenMVS mesh",
        )

    def check_refined_mesh(self, scene: Path) -> None:
        """Validate the refined mesh required by the texturing stage."""

        self._require_file(
            scene.with_name(scene.stem + "_mesh_refine.ply"),
            "OpenMVS refined mesh",
        )

    def check_textured_mesh(self, scene: Path) -> None:
        """Validate the final textured mesh and texture atlas."""

        self._require_file(
            scene.with_name(scene.stem + "_texture.ply"),
            "OpenMVS textured mesh",
        )

        texture_files = list(
            scene.parent.glob(f"{scene.stem}_texture*.png")
        )

        if not texture_files:
            raise RuntimeError(
                "Missing required artifact: OpenMVS texture atlas "
                f"({scene.parent / (scene.stem + '_texture*.png')})"
            )
