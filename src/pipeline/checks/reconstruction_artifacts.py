"""
2x3 - Reconstruction artifacts validation.
"""

from __future__ import annotations

from pathlib import Path


class ReconstructionArtifactCheck:
    """Validates reconstruction artifacts after each stage."""

    def require_files(
        self,
        stage: str,
        files: list[Path],
    ) -> None:
        missing = [path for path in files if not path.exists()]

        if missing:
            missing_text = "\n".join(str(path) for path in missing)
            raise RuntimeError(
                "\n".join(
                    [
                        f"Reconstruction stage failed: {stage}",
                        "Missing artifact(s):",
                        missing_text,
                    ]
                )
            )

    def require_non_empty_directory(
        self,
        stage: str,
        directory: Path,
    ) -> None:
        if not directory.exists():
            raise RuntimeError(
                "\n".join(
                    [
                        f"Reconstruction stage failed: {stage}",
                        f"Missing artifact directory: {directory}",
                    ]
                )
            )

        if not any(directory.iterdir()):
            raise RuntimeError(
                "\n".join(
                    [
                        f"Reconstruction stage failed: {stage}",
                        f"Empty artifact directory: {directory}",
                    ]
                )
            )
