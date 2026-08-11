"""
2x3 - OpenMVS execution wrapper.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


class OpenMVSRunner:
    """
    Gestisce l'esecuzione dei programmi OpenMVS.
    """

    def __init__(self, executable_folder: Path) -> None:
        self.folder = executable_folder

    def executable(self, name: str) -> str:
        executable = self.folder / name

        if os.name == "nt":
            executable = executable.with_suffix(".exe")

        if not executable.exists():
            raise RuntimeError(
                f"Eseguibile OpenMVS non trovato: {executable}"
            )

        return str(executable)

    def run(
        self,
        executable: str,
        arguments: list[str],
    ) -> None:
        """
        Esegue un programma OpenMVS.
        """

        command = [
            self.executable(executable),
            *arguments,
        ]

        print("\n========================================")
        print(f"OpenMVS - {executable}")
        print("========================================")
        print("Command:")
        print(" ".join(command))
        print("")

        result = subprocess.run(
            command,
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
                        f"{executable} terminato con codice {result.returncode}",
                        "",
                        "STDERR:",
                        result.stderr,
                    ]
                )
            )

    def interface_colmap(
        self,
        input_file: Path,
        output_file: Path,
    ) -> None:
        """
        Converte il progetto COLMAP nel formato OpenMVS.
        """

        self.run(
            "InterfaceCOLMAP",
            [
                "-i",
                str(input_file),
                "-o",
                str(output_file),
            ],
        )

    def densify_point_cloud(
        self,
        scene_file: Path,
    ) -> None:
        """
        Genera la nuvola di punti densa.
        """

        self.run(
            "DensifyPointCloud",
            [
                "-i",
                str(scene_file),
            ],
        )

    def reconstruct_mesh(
        self,
        scene_file: Path,
    ) -> None:
        """
        Ricostruisce la mesh dalla nuvola di punti densa.
        """

        dense_cloud = scene_file.with_suffix(".ply")

        self.run(
            "ReconstructMesh",
            [
                "-i",
                str(scene_file),
                "-p",
                str(dense_cloud),
            ],
        )

    def refine_mesh(
        self,
        scene_file: Path,
    ) -> None:
        """
        Raffina la mesh.
        """

        mesh = scene_file.with_name(
            scene_file.stem + "_mesh.ply"
        )

        refined = scene_file.with_name(
            scene_file.stem + "_mesh_refine.mvs"
        )

        self.run(
            "RefineMesh",
            [
                "-i",
                str(scene_file),
                "-m",
                str(mesh),
                "-o",
                str(refined),
            ],
        )
    def texture_mesh(
        self,
        scene_file: Path,
    ) -> None:
        """
        Applica le texture alla mesh raffinata.
        """

        mesh = scene_file.with_name(
            scene_file.stem + "_mesh_refine.ply"
        )

        self.run(
            "TextureMesh",
            [
                "-i",
                str(scene_file),
                "-m",
                str(mesh),
            ],
        )