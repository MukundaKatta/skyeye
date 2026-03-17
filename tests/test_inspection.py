"""Tests for inspection modules."""

from datetime import datetime

import pytest

from skyeye.inspection.flight import FlightPlan
from skyeye.inspection.report import InspectionReport
from skyeye.inspection.tracker import DefectTracker
from skyeye.models import (
    DefectRecord,
    DefectType,
    GeoCoordinate,
    BoundingBox,
    InfrastructureType,
    InspectionMetadata,
    PriorityLevel,
    SeverityLevel,
)


class TestFlightPlan:
    def test_creation(self):
        plan = FlightPlan(
            name="test-flight",
            infrastructure_type=InfrastructureType.BRIDGE,
            altitude=40.0,
        )
        assert plan.total_waypoints == 0
        assert plan.altitude == 40.0

    def test_add_waypoint(self):
        plan = FlightPlan(
            name="test", infrastructure_type=InfrastructureType.BRIDGE
        )
        wp = plan.add_waypoint(latitude=40.0, longitude=-74.0)
        assert plan.total_waypoints == 1
        assert wp.coordinate.latitude == 40.0
        assert wp.capture is True

    def test_capture_count(self):
        plan = FlightPlan(
            name="test", infrastructure_type=InfrastructureType.BRIDGE
        )
        plan.add_waypoint(40.0, -74.0, capture=True)
        plan.add_waypoint(40.001, -74.0, capture=False)
        plan.add_waypoint(40.002, -74.0, capture=True)
        assert plan.capture_count == 2

    def test_generate_grid_pattern(self):
        plan = FlightPlan(
            name="grid-test",
            infrastructure_type=InfrastructureType.BUILDING,
            altitude=30.0,
        )
        center = GeoCoordinate(latitude=40.7128, longitude=-74.0060)
        waypoints = plan.generate_grid_pattern(center, 50.0, 50.0)
        assert len(waypoints) > 0
        assert plan.total_waypoints == len(waypoints)

    def test_estimated_duration(self):
        plan = FlightPlan(
            name="dur-test",
            infrastructure_type=InfrastructureType.BRIDGE,
        )
        plan.add_waypoint(40.0, -74.0)
        plan.add_waypoint(40.001, -74.0)
        duration = plan.estimated_duration_minutes
        assert duration > 0

    def test_haversine(self):
        a = GeoCoordinate(latitude=40.0, longitude=-74.0)
        b = GeoCoordinate(latitude=40.001, longitude=-74.0)
        dist = FlightPlan._haversine(a, b)
        assert 100 < dist < 200  # ~111 meters per 0.001 degree latitude


class TestInspectionReport:
    def _make_report(self) -> InspectionReport:
        return InspectionReport(
            metadata=InspectionMetadata(
                inspection_id="TEST-001",
                infrastructure_type=InfrastructureType.BRIDGE,
            )
        )

    def test_add_finding(self):
        report = self._make_report()
        finding = report.add_finding(
            defect_type=DefectType.CRACK,
            severity=SeverityLevel.MODERATE,
            location_description="Pier 1",
            recommendation="Seal with epoxy.",
        )
        assert finding.id == "F-0001"
        assert finding.priority == PriorityLevel.MEDIUM
        assert len(report.findings) == 1

    def test_critical_findings(self):
        report = self._make_report()
        report.add_finding(DefectType.CRACK, SeverityLevel.MINOR, "Loc A", "Monitor")
        report.add_finding(DefectType.CORROSION, SeverityLevel.CRITICAL, "Loc B", "Replace")
        assert len(report.critical_findings) == 1

    def test_findings_by_severity(self):
        report = self._make_report()
        report.add_finding(DefectType.CRACK, SeverityLevel.MINOR, "A", "Monitor")
        report.add_finding(DefectType.CRACK, SeverityLevel.MINOR, "B", "Monitor")
        report.add_finding(DefectType.CORROSION, SeverityLevel.SEVERE, "C", "Repair")
        by_sev = report.findings_by_severity
        assert len(by_sev[SeverityLevel.MINOR]) == 2
        assert len(by_sev[SeverityLevel.SEVERE]) == 1

    def test_generate_summary(self):
        report = self._make_report()
        report.add_finding(DefectType.CRACK, SeverityLevel.MODERATE, "A", "Fix")
        summary = report.generate_summary()
        assert "TEST-001" in summary
        assert "moderate" in summary

    def test_get_recommendations(self):
        report = self._make_report()
        report.add_finding(DefectType.CRACK, SeverityLevel.CRITICAL, "A", "Urgent fix")
        report.add_finding(DefectType.CRACK, SeverityLevel.MINOR, "B", "Monitor")
        recs = report.get_recommendations()
        assert len(recs) == 2
        assert recs[0].startswith("[URGENT]")


class TestDefectTracker:
    def _make_record(
        self, defect_id: str, date: datetime, severity: SeverityLevel, area: int = 500
    ) -> DefectRecord:
        return DefectRecord(
            defect_id=defect_id,
            inspection_date=date,
            defect_type=DefectType.CRACK,
            severity=severity,
            location=GeoCoordinate(latitude=40.0, longitude=-74.0),
            bounding_box=BoundingBox(x_min=0, y_min=0, x_max=50, y_max=50),
            confidence=0.9,
            area_pixels=area,
        )

    def test_register(self):
        tracker = DefectTracker()
        record = self._make_record("DEF-001", datetime(2024, 1, 1), SeverityLevel.MINOR)
        prog = tracker.register(record)
        assert prog.defect_id == "DEF-001"
        assert len(prog.history) == 1

    def test_worsening_detection(self):
        tracker = DefectTracker()
        tracker.register(self._make_record("DEF-001", datetime(2024, 1, 1), SeverityLevel.MINOR))
        tracker.register(self._make_record("DEF-001", datetime(2024, 6, 1), SeverityLevel.SEVERE))
        assert len(tracker.worsening_defects) == 1

    def test_not_worsening(self):
        tracker = DefectTracker()
        tracker.register(self._make_record("DEF-001", datetime(2024, 1, 1), SeverityLevel.MODERATE))
        tracker.register(self._make_record("DEF-001", datetime(2024, 6, 1), SeverityLevel.MODERATE))
        assert len(tracker.worsening_defects) == 0

    def test_area_growth_rate(self):
        tracker = DefectTracker()
        tracker.register(self._make_record("DEF-001", datetime(2024, 1, 1), SeverityLevel.MINOR, area=100))
        tracker.register(self._make_record("DEF-001", datetime(2024, 4, 1), SeverityLevel.MINOR, area=200))
        prog = tracker.get_progression("DEF-001")
        assert prog is not None
        rate = prog.area_growth_rate
        assert rate is not None
        assert rate > 0

    def test_generate_id(self):
        tracker = DefectTracker()
        id1 = tracker.generate_id()
        id2 = tracker.generate_id()
        assert id1 != id2
        assert id1.startswith("DEF-")

    def test_get_summary(self):
        tracker = DefectTracker()
        tracker.register(self._make_record("DEF-001", datetime(2024, 1, 1), SeverityLevel.MINOR))
        tracker.register(self._make_record("DEF-002", datetime(2024, 1, 1), SeverityLevel.SEVERE))
        summary = tracker.get_summary()
        assert summary["minor"] == 1
        assert summary["severe"] == 1

    def test_get_by_severity(self):
        tracker = DefectTracker()
        tracker.register(self._make_record("DEF-001", datetime(2024, 1, 1), SeverityLevel.MINOR))
        tracker.register(self._make_record("DEF-002", datetime(2024, 1, 1), SeverityLevel.MINOR))
        tracker.register(self._make_record("DEF-003", datetime(2024, 1, 1), SeverityLevel.SEVERE))
        minor = tracker.get_by_severity(SeverityLevel.MINOR)
        assert len(minor) == 2
