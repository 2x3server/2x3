"""
2x3 - Reconstruction artifact validation.
"""

from __future__ import annotations

from pathlib import Path


class ReconstructionArtifactCheck:
    """Verifies that expected reconstruction artifacts exist after each stage."""

    def check(self, stage: str, artifacts: list[Path]) -> None:
        """
        Assert that all expected artifacts for a reconstruction stage exist.

        Parameters
        ----------
        stage:
            Name of the reconstruction stage (used in the error message).
        artifacts:
            List of file paths that must exist after the stage completes.

        Raises
        ------
        RuntimeError
            If any expected artifact is missing.  The error message identifies
            both the missing artifact and the stage that produced it.
        """

        for path in artifacts:
            if not path.exists():
                raise RuntimeError(
                    f"Reconstruction artifact missing after stage '{stage}': "
                    f"{path}"
                )
