"""
2x3 - Application entry point.
"""

from __future__ import annotations

from .configuration_manager import ConfigurationManager
from .project_manager import ProjectManager
from ..pipeline.pipeline import Pipeline


class Application:
    """Main application."""

    def __init__(self) -> None:
        self.configuration = ConfigurationManager()
        self.project_manager = ProjectManager()

    def run(self) -> None:
        project = self.project_manager.create_project(
            self.configuration.default_project_path
        )

        pipeline = Pipeline(
            project,
            self.configuration,
        )

        pipeline.run()


def start_application() -> None:
    """Application entry point."""

    app = Application()
    app.run()