"""
2x3 - Application configuration manager.
"""

from __future__ import annotations

from pathlib import Path


class ConfigurationManager:
    """Manages the application configuration."""

    def __init__(self) -> None:
        """Initialize default configuration."""

        self.projects_root = Path("data/projects")
        self.default_project_name = "demo"

        # OpenMVS
        self.openmvs_executable_folder = Path(
            "/workspaces/openMVS/build-vcpkg/bin"
        )

        # Video
        self.frame_step = 30

        # Image quality
        self.laplacian_threshold = 5.0
        self.minimum_width = 640
        self.minimum_height = 480

        # Supported formats
        self.supported_formats = {
            "JPEG",
            "PNG",
            "BMP",
            "TIFF",
            "WEBP",
        }

        self.supported_modes = {
            "RGB",
            "RGBA",
            "L",
        }

        # Application
        self.language = "it"
        self.theme = "system"

    @property
    def default_project_path(self) -> Path:
        """Return the default project path."""

        return self.projects_root / self.default_project_name