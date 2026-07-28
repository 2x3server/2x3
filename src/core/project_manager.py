"""
2x3 - Project manager.
"""

from __future__ import annotations

from pathlib import Path

from ..models.project import Project


class ProjectManager:
    """Manages the lifecycle of projects."""

    def __init__(self) -> None:
        """Initialize the manager."""

        self._current_project: Project | None = None

    @property
    def current_project(self) -> Project:
        """Return the current project."""

        if self._current_project is None:
            raise RuntimeError("No project is currently open.")

        return self._current_project

    def create_project(self, project_path: Path) -> Project:
        """Create a new project and make it the current one."""

        project = Project(project_path)
        project.create_structure()

        self._current_project = project

        return project

    def open_project(self, project_path: Path) -> Project:
        """Open an existing project."""

        project = Project(project_path)

        self._current_project = project

        return project