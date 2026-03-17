"""Tests for report generation."""

import pytest

from skyeye.inspection.report import InspectionReport
from skyeye.models import (
    DefectType,
    InfrastructureType,
    InspectionMetadata,
    SeverityLevel,
)
from skyeye.report import ReportFormatter


class TestReportFormatter:
    def _make_report(self) -> InspectionReport:
        report = InspectionReport(
            metadata=InspectionMetadata(
                inspection_id="RPT-TEST",
                infrastructure_type=InfrastructureType.BRIDGE,
                total_images=50,
            )
        )
        report.add_finding(DefectType.CRACK, SeverityLevel.MINOR, "Deck surface", "Monitor")
        report.add_finding(DefectType.CORROSION, SeverityLevel.SEVERE, "Pier 2", "Repair steel")
        report.add_finding(DefectType.SPALLING, SeverityLevel.CRITICAL, "Abutment", "Emergency repair")
        report.generate_summary()
        return report

    def test_render_to_text(self):
        report = self._make_report()
        formatter = ReportFormatter()
        text = formatter.render_to_text(report)
        assert "RPT-TEST" in text
        assert "SKYEYE" in text
        assert "crack" in text
        assert "FINDINGS" in text
        assert "RECOMMENDATIONS" in text

    def test_render_to_text_no_findings(self):
        report = InspectionReport(
            metadata=InspectionMetadata(
                inspection_id="EMPTY",
                infrastructure_type=InfrastructureType.BUILDING,
            )
        )
        formatter = ReportFormatter()
        text = formatter.render_to_text(report)
        assert "No defects detected" in text

    def test_save_to_file(self, tmp_path):
        report = self._make_report()
        formatter = ReportFormatter()
        out = formatter.save_to_file(report, str(tmp_path / "output" / "report.txt"))
        assert out.exists()
        content = out.read_text()
        assert "RPT-TEST" in content

    def test_render_to_console(self):
        """Smoke test that console rendering does not raise."""
        from rich.console import Console

        report = self._make_report()
        formatter = ReportFormatter(console=Console(file=open("/dev/null", "w")))
        formatter.render_to_console(report)  # Should not raise
