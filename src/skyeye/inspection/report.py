"""Inspection report builder with findings, recommendations, and priorities."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from skyeye.models import (
    DefectType,
    Detection,
    Finding,
    InfrastructureType,
    InspectionMetadata,
    PriorityLevel,
    SeverityLevel,
)


class InspectionReport(BaseModel):
    """Structured inspection report aggregating findings and recommendations.

    Collects detection results, assigns priorities, and generates
    actionable recommendations for infrastructure maintenance.
    """

    metadata: InspectionMetadata
    findings: list[Finding] = Field(default_factory=list)
    summary: Optional[str] = None
    overall_condition: Optional[str] = None
    next_inspection_date: Optional[datetime] = None

    @property
    def critical_findings(self) -> list[Finding]:
        """Findings with critical severity."""
        return [f for f in self.findings if f.severity == SeverityLevel.CRITICAL]

    @property
    def urgent_findings(self) -> list[Finding]:
        """Findings with urgent priority."""
        return [f for f in self.findings if f.priority == PriorityLevel.URGENT]

    @property
    def findings_by_severity(self) -> dict[SeverityLevel, list[Finding]]:
        """Group findings by severity level."""
        grouped: dict[SeverityLevel, list[Finding]] = {level: [] for level in SeverityLevel}
        for finding in self.findings:
            grouped[finding.severity].append(finding)
        return grouped

    @property
    def findings_by_type(self) -> dict[DefectType, list[Finding]]:
        """Group findings by defect type."""
        grouped: dict[DefectType, list[Finding]] = {dt: [] for dt in DefectType}
        for finding in self.findings:
            grouped[finding.defect_type].append(finding)
        return grouped

    def add_finding(
        self,
        defect_type: DefectType,
        severity: SeverityLevel,
        location_description: str,
        recommendation: str,
        priority: Optional[PriorityLevel] = None,
        image_references: Optional[list[str]] = None,
        detection: Optional[Detection] = None,
    ) -> Finding:
        """Add a finding to the report.

        If priority is not specified it is inferred from severity.

        Returns:
            The created Finding.
        """
        if priority is None:
            priority = self._severity_to_priority(severity)

        finding = Finding(
            id=f"F-{len(self.findings) + 1:04d}",
            defect_type=defect_type,
            severity=severity,
            priority=priority,
            location_description=location_description,
            recommendation=recommendation,
            image_references=image_references or [],
            detection=detection,
        )
        self.findings.append(finding)
        return finding

    def generate_summary(self) -> str:
        """Auto-generate a textual summary of the inspection."""
        total = len(self.findings)
        by_sev = self.findings_by_severity
        lines = [
            f"Inspection Report: {self.metadata.inspection_id}",
            f"Date: {self.metadata.date.strftime('%Y-%m-%d')}",
            f"Infrastructure: {self.metadata.infrastructure_type.value}",
            f"Total findings: {total}",
        ]
        for level in SeverityLevel:
            count = len(by_sev[level])
            if count:
                lines.append(f"  {level.value}: {count}")

        if by_sev[SeverityLevel.CRITICAL]:
            lines.append("\nIMMEDIATE ACTION REQUIRED - Critical defects detected.")
        elif by_sev[SeverityLevel.SEVERE]:
            lines.append("\nRepair recommended within 30 days.")
        elif by_sev[SeverityLevel.MODERATE]:
            lines.append("\nSchedule maintenance within 90 days.")
        else:
            lines.append("\nInfrastructure in acceptable condition.")

        self.summary = "\n".join(lines)
        return self.summary

    def get_recommendations(self) -> list[str]:
        """Collect all unique recommendations sorted by priority."""
        priority_order = {
            PriorityLevel.URGENT: 0,
            PriorityLevel.HIGH: 1,
            PriorityLevel.MEDIUM: 2,
            PriorityLevel.LOW: 3,
        }
        sorted_findings = sorted(
            self.findings, key=lambda f: priority_order.get(f.priority, 99)
        )
        seen: set[str] = set()
        recs: list[str] = []
        for f in sorted_findings:
            if f.recommendation not in seen:
                seen.add(f.recommendation)
                recs.append(f"[{f.priority.value.upper()}] {f.recommendation}")
        return recs

    @staticmethod
    def _severity_to_priority(severity: SeverityLevel) -> PriorityLevel:
        mapping = {
            SeverityLevel.MINOR: PriorityLevel.LOW,
            SeverityLevel.MODERATE: PriorityLevel.MEDIUM,
            SeverityLevel.SEVERE: PriorityLevel.HIGH,
            SeverityLevel.CRITICAL: PriorityLevel.URGENT,
        }
        return mapping[severity]
