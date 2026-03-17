"""Defect progression tracker for monitoring changes over time."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from skyeye.models import DefectRecord, DefectType, SeverityLevel


class ProgressionEntry(BaseModel):
    """A snapshot of a defect at a point in time."""

    date: datetime
    severity: SeverityLevel
    area_pixels: int
    confidence: float


class DefectProgression(BaseModel):
    """Track a single defect's history across inspections."""

    defect_id: str
    defect_type: DefectType
    history: list[ProgressionEntry] = Field(default_factory=list)

    @property
    def first_seen(self) -> Optional[datetime]:
        return self.history[0].date if self.history else None

    @property
    def last_seen(self) -> Optional[datetime]:
        return self.history[-1].date if self.history else None

    @property
    def current_severity(self) -> Optional[SeverityLevel]:
        return self.history[-1].severity if self.history else None

    @property
    def is_worsening(self) -> bool:
        """Check if defect severity has increased over time."""
        if len(self.history) < 2:
            return False
        severity_order = list(SeverityLevel)
        first_idx = severity_order.index(self.history[0].severity)
        last_idx = severity_order.index(self.history[-1].severity)
        return last_idx > first_idx

    @property
    def area_growth_rate(self) -> Optional[float]:
        """Compute area growth rate in pixels per day."""
        if len(self.history) < 2:
            return None
        first = self.history[0]
        last = self.history[-1]
        days = (last.date - first.date).total_seconds() / 86400
        if days <= 0:
            return None
        return (last.area_pixels - first.area_pixels) / days


class DefectTracker:
    """Monitor defect progression over multiple inspections.

    Maintains a registry of known defects and matches new observations
    to existing records, enabling trend analysis and predictive
    maintenance scheduling.
    """

    def __init__(self, distance_threshold: float = 50.0) -> None:
        """Initialize tracker.

        Args:
            distance_threshold: Maximum pixel distance to consider
                two detections as the same defect.
        """
        self.distance_threshold = distance_threshold
        self._progressions: dict[str, DefectProgression] = {}
        self._next_id: int = 1

    @property
    def tracked_defects(self) -> dict[str, DefectProgression]:
        """All tracked defect progressions."""
        return dict(self._progressions)

    @property
    def worsening_defects(self) -> list[DefectProgression]:
        """Defects whose severity has increased over time."""
        return [p for p in self._progressions.values() if p.is_worsening]

    def register(self, record: DefectRecord) -> DefectProgression:
        """Register a defect observation.

        Matches to an existing defect by ID or creates a new progression.

        Args:
            record: The defect observation to register.

        Returns:
            The DefectProgression the record was added to.
        """
        defect_id = record.defect_id

        if defect_id not in self._progressions:
            self._progressions[defect_id] = DefectProgression(
                defect_id=defect_id,
                defect_type=record.defect_type,
            )

        progression = self._progressions[defect_id]
        entry = ProgressionEntry(
            date=record.inspection_date,
            severity=record.severity,
            area_pixels=record.area_pixels,
            confidence=record.confidence,
        )
        progression.history.append(entry)
        progression.history.sort(key=lambda e: e.date)
        return progression

    def register_batch(self, records: list[DefectRecord]) -> list[DefectProgression]:
        """Register multiple defect observations."""
        return [self.register(r) for r in records]

    def generate_id(self) -> str:
        """Generate a unique defect identifier."""
        defect_id = f"DEF-{self._next_id:06d}"
        self._next_id += 1
        return defect_id

    def get_progression(self, defect_id: str) -> Optional[DefectProgression]:
        """Retrieve the progression history for a defect."""
        return self._progressions.get(defect_id)

    def get_by_severity(self, severity: SeverityLevel) -> list[DefectProgression]:
        """Get all defects currently at a given severity level."""
        return [
            p
            for p in self._progressions.values()
            if p.current_severity == severity
        ]

    def get_summary(self) -> dict[str, int]:
        """Summarize tracked defects by current severity."""
        summary: dict[str, int] = {level.value: 0 for level in SeverityLevel}
        for prog in self._progressions.values():
            if prog.current_severity:
                summary[prog.current_severity.value] += 1
        return summary
