"""Tests for the inspection simulator."""

import numpy as np
import pytest

from skyeye.models import DefectType, SeverityLevel
from skyeye.simulator import InspectionSimulator


class TestInspectionSimulator:
    def test_reproducibility(self):
        sim1 = InspectionSimulator(seed=42)
        sim2 = InspectionSimulator(seed=42)
        dets1 = sim1.generate_detections(count=10)
        dets2 = sim2.generate_detections(count=10)
        for d1, d2 in zip(dets1, dets2):
            assert d1.defect_type == d2.defect_type
            assert d1.confidence == d2.confidence

    def test_generate_image(self):
        sim = InspectionSimulator(seed=0)
        image = sim.generate_image(128, 128, num_defects=3)
        assert image.shape == (128, 128, 3)
        assert image.dtype == np.uint8

    def test_generate_detections(self):
        sim = InspectionSimulator(seed=0)
        dets = sim.generate_detections(count=20)
        assert len(dets) == 20
        for det in dets:
            assert 0.5 <= det.confidence <= 0.99
            assert det.bounding_box.x_min < det.bounding_box.x_max

    def test_generate_detections_filtered(self):
        sim = InspectionSimulator(seed=0)
        dets = sim.generate_detections(
            count=30, defect_types=[DefectType.CRACK, DefectType.CORROSION]
        )
        for det in dets:
            assert det.defect_type in (DefectType.CRACK, DefectType.CORROSION)

    def test_generate_defect_records(self):
        sim = InspectionSimulator(seed=0)
        records = sim.generate_defect_records(num_defects=3, num_inspections=4)
        assert len(records) == 12  # 3 defects * 4 inspections
        # Check that each defect has 4 records
        ids = set(r.defect_id for r in records)
        assert len(ids) == 3

    def test_generate_defect_records_dates(self):
        from datetime import datetime

        sim = InspectionSimulator(seed=0)
        start = datetime(2024, 1, 1)
        records = sim.generate_defect_records(
            num_defects=1, num_inspections=3, start_date=start, interval_days=30
        )
        dates = sorted(set(r.inspection_date for r in records))
        assert len(dates) == 3
        assert dates[0] == start
