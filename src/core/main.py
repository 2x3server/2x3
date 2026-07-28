"""
2x3 - Open Source Video/Image to 3D Reconstruction

Main entry point of the application.
"""

from __future__ import annotations

from .application import start_application


def main() -> None:
    """Start the application."""

    start_application()


if __name__ == "__main__":
    main()