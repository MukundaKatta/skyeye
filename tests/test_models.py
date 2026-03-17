"""Tests for SKYEYE data models."""

import pytest
from pydantic import ValidationError

from skyeye.models import (
    BoundingBox,
    DefectType,
    Detection,
    Finding,
    GeoCoordinate,
    InfrastructureType,
    InspectionMetadata,
    PriorityLevel,
    SegmentationMask,
    SeverityLevel,
    Waypoint,
)


class TestBoundingBox:
    def test_properties(self):
        bb = BoundingBox(x_min=10, y_min=20, x_max=50, y_max=80)
        assert bb.width == 40
        assert bb.height == 60
        assert bb.area == 2400
        assert bb.center == (30.0, 50.0)

    def test_validation_rejects_negative(self):
        with pytest.raises(ValidationError):
            BoundingBox(x_min=-1, y_min=0, x_max=10, y_max=10)


class TestGeoCoordinate:
    def test_valid_coordinate(self):
        coord = GeoCoordinate(latitude=40.7128, longitude=-74.0060, altitude=30.0)
        assert coord.latitude == 40.7128
        assert coord.longitude == -74.0060

    def test_invalid_latitude(self):
        with pytest.raises(ValidationError):
            GeoCoordinate(latitude=91, longitude=0)

    def test_invalid_longitude(self):
        with pytest.raises(ValidationError):
            GeoCoordinate(latitude=0, longitude=181)


class TestDetection:
    def test_creation(self):
        det = Detection(
            defect_type=DefectType.CRACK,
            confidence=0.95,
            bounding_box=BoundingBox(x_min=0, y_min=0, x_max=100, y_max=100),
        )
        assert det.defect_type == DefectType.CRACK
        assert det.confidence == 0.95
        assert det.severity is None

    def test_confidence_range(self):
        with pytest.raises(ValidationError):
            Detection(
                defect_type=DefectType.CRACK,
                confidence=1.5,
                bounding_box=BoundingBox(x_min=0, y_min=0, x_max=10, y_max=10),
            )


class TestSegmentationMask:
    def test_creation(self):
        mask = SegmentationMask(
            width=256, height=256,
            defect_type=DefectType.CORROSION,
            pixel_count=1000,
            coverage_ratio=0.0153,
        )
        assert mask.pixel_count == 1000


class TestWaypoint:
    def test_creation(self):
        wp = Waypoint(
            id=1,
            coordinate=GeoCoordinate(latitude=40.0, longitude=-74.0, altitude=30.0),
            heading=90.0,
        )
        assert wp.heading == 90.0
        assert wp.capture is True


class TestFinding:
    def test_creation(self):
        finding = Finding(
            id="F-0001",
            defect_type=DefectType.SPALLING,
            severity=SeverityLevel.MODERATE,
            priority=PriorityLevel.MEDIUM,
            location_description="South abutment",
            recommendation="Patch repair needed.",
        )
        assert finding.severity == SeverityLevel.MODERATE


class TestInspectionMetadata:
    def test_defaults(self):
        meta = InspectionMetadata(
            inspection_id="TEST-001",
            infrastructure_type=InfrastructureType.BRIDGE,
        )
        assert meta.total_images == 0
        assert meta.inspector is None


class TestEnums:
    def test_defect_types(self):
        assert len(DefectType) == 5
        assert DefectType.CRACK.value == "crack"
        assert DefectType.VEGETATION_GROWTH.value == "vegetation_growth"

    def test_severity_levels(self):
        assert len(SeverityLevel) == 4
        levels = list(SeverityLevel)
        assert levels[0] == SeverityLevel.MINOR
        assert levels[-1] == SeverityLevel.CRITICAL

    def test_infrastructure_types(self):
        assert len(InfrastructureType) == 3
