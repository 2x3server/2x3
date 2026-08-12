from __future__ import annotations

import struct
from pathlib import Path


class STLExporter:
    """Converte una mesh PLY binary_little_endian in STL binary."""

    def export(self, ply_file: Path, stl_file: Path) -> Path:
        if not ply_file.exists():
            raise FileNotFoundError(
                f"Mesh PLY non trovata: {ply_file}"
            )

        data = ply_file.read_bytes()

        if not data.startswith(b"ply"):
            raise ValueError(
                f"File non riconosciuto come PLY: {ply_file}"
            )

        header_end = data.index(b"end_header") + len(b"end_header")

        while data[header_end:header_end + 1] in (b"\n", b"\r"):
            header_end += 1

        header = data[:header_end].decode(
            "ascii",
            errors="replace",
        )

        if "format binary_little_endian 1.0" not in header:
            raise ValueError(
                "STLExporter supporta attualmente solo "
                "PLY binary_little_endian 1.0"
            )

        vertex_count = self._read_count(header, "vertex")
        face_count = self._read_count(header, "face")

        offset = header_end
        vertices: list[tuple[float, float, float]] = []

        for _ in range(vertex_count):
            x, y, z = struct.unpack_from("<fff", data, offset)
            vertices.append((x, y, z))
            offset += 12

        triangles: list[tuple[int, int, int]] = []

        for _ in range(face_count):
            count = struct.unpack_from("<B", data, offset)[0]
            offset += 1

            indices = struct.unpack_from(
                "<" + ("I" * count),
                data,
                offset,
            )
            offset += 4 * count

            if count == 3:
                triangles.append(
                    (indices[0], indices[1], indices[2])
                )

        stl_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with stl_file.open("wb") as output:
            output.write(
                b"2x3 STL export".ljust(80, b"\0")
            )
            output.write(
                struct.pack("<I", len(triangles))
            )

            for a, b, c in triangles:
                v1 = vertices[a]
                v2 = vertices[b]
                v3 = vertices[c]

                output.write(
                    struct.pack(
                        "<12fH",
                        0.0,
                        0.0,
                        0.0,
                        *v1,
                        *v2,
                        *v3,
                        0,
                    )
                )

        print(
            f"STL exported: {stl_file} "
            f"({len(triangles)} triangles)"
        )

        return stl_file

    @staticmethod
    def _read_count(header: str, element: str) -> int:
        prefix = f"element {element} "

        for line in header.splitlines():
            if line.startswith(prefix):
                return int(line[len(prefix):].strip())

        raise ValueError(
            f"Elemento PLY non trovato: {element}"
        )
