from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class ColmapRunner:
    """
    Gestisce l'esecuzione dei comandi COLMAP.
    """

    def __init__(self) -> None:
        executable = shutil.which("colmap")

        if executable is None:
            raise RuntimeError(
                "COLMAP non è installato oppure non è presente nel PATH."
            )

        self.executable = executable

    def run(self, arguments: list[str]) -> None:
        command = [self.executable] + arguments

        print("\n========================================")
        print("COLMAP")
        print("========================================")
        print("Command:")
        print(" ".join(command))
        print("")

        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "offscreen"

        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
        )

        if result.stdout.strip():
            print(result.stdout)

        if result.stderr.strip():
            print(result.stderr)

        if result.returncode != 0:
            raise RuntimeError(
                "\n".join(
                    [
                        f"COLMAP ha terminato con codice {result.returncode}",
                        "",
                        "STDERR:",
                        result.stderr,
                    ]
                )
            )

    def feature_extractor(
        self,
        image_path: Path,
        database_path: Path,
    ) -> None:

        database_path.parent.mkdir(parents=True, exist_ok=True)

        self.run(
            [
                "feature_extractor",
                "--ImageReader.single_camera",
                "1",
                "--SiftExtraction.use_gpu",
                "0",
                "--database_path",
                str(database_path),
                "--image_path",
                str(image_path),
            ]
        )

    def exhaustive_matcher(
        self,
        database_path: Path,
    ) -> None:

        self.run(
            [
                "exhaustive_matcher",
                "--SiftMatching.use_gpu",
                "0",
                "--database_path",
                str(database_path),
            ]
        )

    def mapper(
        self,
        image_path: Path,
        database_path: Path,
        output_path: Path,
    ) -> None:

        output_path.mkdir(parents=True, exist_ok=True)

        self.run(
            [
                "mapper",
                "--database_path",
                str(database_path),
                "--image_path",
                str(image_path),
                "--output_path",
                str(output_path),
            ]
        )

    def image_undistorter(
        self,
        image_path: Path,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """
        Create the undistorted images required for dense reconstruction.
        """

        output_path.mkdir(parents=True, exist_ok=True)

        self.run(
            [
                "image_undistorter",
                "--image_path",
                str(image_path),
                "--input_path",
                str(input_path),
                "--output_path",
                str(output_path),
                "--output_type",
                "COLMAP",
            ]
        )

    def patch_match_stereo(
        self,
        workspace_path: Path,
    ) -> None:
        """
        Esegue la ricostruzione densa mediante Patch Match Stereo.
        """

        self.run(
            [
                "patch_match_stereo",
                "--workspace_path",
                str(workspace_path),
                "--workspace_format",
                "COLMAP",
            ]
        )