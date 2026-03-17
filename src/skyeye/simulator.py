"""Simulator for generating synthetic inspection data and testing pipelines."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from skyeye.models import (
    BoundingBox,
    DefectRecord,
    DefectType,
    Detection,
    GeoCoordinate,
    SeverityLevel,
)


class InspectionSimulator:
    """Generate synthetic drone inspection data for testing and development.

    Simulates defect detections, severity distributions, and
    multi-inspection progression scenarios without requiring
    real drone hardware or field data.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize the simulator.

        Args:
            seed: Random seed for reproducible simulations.
        """
        self.rng = random.Random(seed)
        self.np_rng = np.random.RandomState(seed)

    def generate_image(
        self,
        height: int = 256,
        width: int = 256,
        num_defects: int = 0,
    ) -> np.ndarray:
        """Generate a synthetic inspection image.

        Creates a random background with optional synthetic defect
        patterns overlaid.

        Args:
            height: Image height in pixels.
            width: Image width in pixels.
            num_defects: Number of synthetic defect regions to add.

        Returns:
            Synthetic image as uint8 array of shape (H, W, 3).
        """
        # Generate a concrete-like background texture
        base_color = self.np_rng.randint(140, 200, size=3)
        image = self.np_rng.normal(
            loc=base_color, scale=15, size=(height, width, 3)
        ).astype(np.float64)

        for _ in range(num_defects):
            defect_type = self.rng.choice(list(DefectType))
            cx = self.rng.randint(20, width - 20)
            cy = self.rng.randint(20, height - 20)
            radius = self.rng.randint(10, 40)
            self._draw_defect(image, cx, cy, radius, defect_type)

        return np.clip(image, 0, 255).astype(np.uint8)

    def generate_detections(
        self,
        count: int = 5,
        defect_types: Optional[list[DefectType]] = None,
        image_width: int = 1920,
        image_height: int = 1080,
    ) -> list[Detection]:
        """Generate synthetic detection results.

        Args:
            count: Number of detections to generate.
            defect_types: Restrict to specific defect types. If None, all types.
            image_width: Width of the simulated image.
            image_height: Height of the simulated image.

        Returns:
            List of synthetic Detection objects.
        """
        types = defect_types or list(DefectType)
        detections: list[Detection] = []

        for _ in range(count):
            w = self.rng.uniform(20, image_width * 0.3)
            h = self.rng.uniform(20, image_height * 0.3)
            x1 = self.rng.uniform(0, image_width - w)
            y1 = self.rng.uniform(0, image_height - h)

            detections.append(
                Detection(
                    defect_type=self.rng.choice(types),
                    confidence=round(self.rng.uniform(0.5, 0.99), 4),
                    bounding_box=BoundingBox(
                        x_min=round(x1, 2),
                        y_min=round(y1, 2),
                        x_max=round(x1 + w, 2),
                        y_max=round(y1 + h, 2),
                    ),
                )
            )
        return detections

    def generate_defect_records(
        self,
        num_defects: int = 5,
        num_inspections: int = 3,
        start_date: Optional[datetime] = None,
        interval_days: int = 90,
    ) -> list[DefectRecord]:
        """Generate synthetic defect records over multiple inspections.

        Simulates defect progression where severity may increase over time.

        Args:
            num_defects: Number of unique defects to simulate.
            num_inspections: Number of inspection dates.
            start_date: Date of first inspection.
            interval_days: Days between inspections.

        Returns:
            List of DefectRecord objects across all inspections.
        """
        if start_date is None:
            start_date = datetime(2024, 1, 1)

        severity_levels = list(SeverityLevel)
        records: list[DefectRecord] = []

        for d in range(num_defects):
            defect_id = f"DEF-{d + 1:06d}"
            defect_type = self.rng.choice(list(DefectType))
            base_severity_idx = self.rng.randint(0, 2)
            base_area = self.rng.randint(100, 5000)

            lat = self.rng.uniform(40.0, 41.0)
            lon = self.rng.uniform(-74.5, -73.5)

            for i in range(num_inspections):
                inspection_date = start_date + timedelta(days=i * interval_days)
                sev_idx = min(base_severity_idx + self.rng.randint(0, 1), len(severity_levels) - 1)
                area = int(base_area * (1 + 0.1 * i * self.rng.random()))

                records.append(
                    DefectRecord(
                        defect_id=defect_id,
                        inspection_date=inspection_date,
                        defect_type=defect_type,
                        severity=severity_levels[sev_idx],
                        location=GeoCoordinate(latitude=lat, longitude=lon),
                        bounding_box=BoundingBox(
                            x_min=100.0, y_min=100.0,
                            x_max=100.0 + area ** 0.5,
                            y_max=100.0 + area ** 0.5,
                        ),
                        confidence=round(self.rng.uniform(0.7, 0.99), 4),
                        area_pixels=area,
                    )
                )
        return records

    def _draw_defect(
        self,
        image: np.ndarray,
        cx: int,
        cy: int,
        radius: int,
        defect_type: DefectType,
    ) -> None:
        """Draw a simple synthetic defect pattern onto an image."""
        h, w = image.shape[:2]
        y_coords, x_coords = np.ogrid[
            max(0, cy - radius): min(h, cy + radius),
            max(0, cx - radius): min(w, cx + radius),
        ]
        mask = ((x_coords - cx) ** 2 + (y_coords - cy) ** 2) <= radius ** 2

        if defect_type == DefectType.CRACK:
            image[max(0, cy - radius): min(h, cy + radius),
                  max(0, cx - radius): min(w, cx + radius)][mask] *= 0.3
        elif defect_type == DefectType.CORROSION:
            region = image[max(0, cy - radius): min(h, cy + radius),
                          max(0, cx - radius): min(w, cx + radius)]
            region[mask] = [139, 90, 43]
        elif defect_type == DefectType.SPALLING:
            region = image[max(0, cy - radius): min(h, cy + radius),
                          max(0, cx - radius): min(w, cx + radius)]
            region[mask] = region[mask] * 0.6 + self.np_rng.normal(0, 20, region[mask].shape)
        elif defect_type == DefectType.DEFORMATION:
            pass  # Deformation is geometric, hard to simulate on a flat image
        elif defect_type == DefectType.VEGETATION_GROWTH:
            region = image[max(0, cy - radius): min(h, cy + radius),
                          max(0, cx - radius): min(w, cx + radius)]
            region[mask] = [34, 120, 50]
