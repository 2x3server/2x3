"""
2x3 - Image Quality Checker.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import cv2
from PIL import Image

from ..core.configuration_manager import ConfigurationManager
from ..models.quality_report import QualityReport


class ImageQualityChecker:
    """Performs quality checks on imported images."""

    def __init__(self, configuration: ConfigurationManager) -> None:
        self.configuration = configuration

    @staticmethod
    def _laplacian_variance(image_path: Path) -> float:
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise RuntimeError("Unable to load image with OpenCV.")

        return float(cv2.Laplacian(image, cv2.CV_64F).var())

    def check(self, images: list[Path]) -> QualityReport:
        """Validate the imported dataset."""

        report = QualityReport()

        print("\nImage Quality Report")
        print("--------------------")
        print(f"Images found: {len(images)}")

        if not images:
            report.reason = "No images available."

            print("Status: FAILED")
            print(f"Reason: {report.reason}")

            return report

        format_counter = Counter()
        mode_counter = Counter()

        min_width = None
        min_height = None
        max_width = 0
        max_height = 0

        for image_path in images:

            try:

                with Image.open(image_path) as img:

                    image_format = img.format

                    if image_format not in self.configuration.supported_formats:
                        print(f"Skipped (format): {image_path.name}")
                        report.rejected_images += 1
                        continue

                    image_mode = img.mode

                    if image_mode not in self.configuration.supported_modes:
                        print(f"Skipped (mode): {image_path.name}")
                        report.rejected_images += 1
                        continue

                    width, height = img.size

                    if (
                        width < self.configuration.minimum_width
                        or height < self.configuration.minimum_height
                    ):
                        print(f"Skipped (size): {image_path.name}")
                        report.rejected_images += 1
                        continue

                    sharpness = self._laplacian_variance(image_path)

                    print(
                        f"{image_path.name}: "
                        f"Laplacian variance = {sharpness:.2f}"
                    )

                    if (
                        sharpness
                        < self.configuration.laplacian_threshold
                    ):
                        print(f"Skipped (blurry): {image_path.name}")
                        report.rejected_images += 1
                        continue

                    img.verify()

                    report.valid_images.append(image_path)

                    format_counter[image_format] += 1
                    mode_counter[image_mode] += 1

                    if min_width is None or width < min_width:
                        min_width = width

                    if min_height is None or height < min_height:
                        min_height = height

                    max_width = max(max_width, width)
                    max_height = max(max_height, height)

            except Exception as error:
                print(f"Skipped (error): {image_path.name}")
                print(error)
                report.rejected_images += 1

        print("\nDataset Statistics")
        print("------------------")

        print(f"Valid images: {len(report.valid_images)}")
        print(f"Rejected images: {report.rejected_images}")

        if not report.valid_images:
            report.reason = "No valid images available."

            print("Status: FAILED")
            print(f"Reason: {report.reason}")

            return report

        report.formats = dict(format_counter)
        report.modes = dict(mode_counter)
        report.minimum_resolution = (min_width, min_height)
        report.maximum_resolution = (max_width, max_height)
        report.status = "PASSED"

        print("Formats:", report.formats)
        print("Modes:", report.modes)
        print(
            f"Minimum resolution: "
            f"{min_width}x{min_height}"
        )
        print(
            f"Maximum resolution: "
            f"{max_width}x{max_height}"
        )
        print("Status: PASSED")

        return report