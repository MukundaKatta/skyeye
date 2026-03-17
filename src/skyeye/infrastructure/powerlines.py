"""Powerline inspection standards and protocols."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from skyeye.models import DefectType, GeoCoordinate, InfrastructureType, SeverityLevel


class PowerlineSpan(BaseModel):
    """A span between two towers or poles."""

    span_id: str
    start_tower: str
    end_tower: str
    length_m: float = Field(gt=0)
    voltage_kv: float = Field(gt=0)
    conductor_type: str = Field(default="ACSR")
    num_circuits: int = Field(default=1, ge=1)


class TowerProfile(BaseModel):
    """Profile of a transmission tower or pole."""

    tower_id: str
    location: Optional[GeoCoordinate] = None
    height_m: float = Field(gt=0)
    tower_type: str = Field(default="lattice")  # lattice, monopole, wood_pole, h-frame
    material: str = Field(default="steel")


class PowerlineProfile(BaseModel):
    """Profile of a powerline corridor for inspection."""

    corridor_id: str
    name: str
    voltage_kv: float = Field(gt=0)
    total_length_km: float = Field(gt=0)
    towers: list[TowerProfile] = Field(default_factory=list)
    spans: list[PowerlineSpan] = Field(default_factory=list)


class PowerlineInspection:
    """Powerline-specific inspection standards and defect assessment.

    Covers conductor inspection, tower structural assessment,
    insulator condition, and vegetation encroachment detection.
    """

    INFRASTRUCTURE_TYPE = InfrastructureType.POWERLINE

    RELEVANT_DEFECTS: list[DefectType] = [
        DefectType.CORROSION,
        DefectType.DEFORMATION,
        DefectType.VEGETATION_GROWTH,
        DefectType.CRACK,
        DefectType.SPALLING,
    ]

    # Vegetation clearance thresholds in meters
    VEGETATION_CLEARANCE: dict[str, float] = {
        "low_voltage": 3.0,
        "medium_voltage": 5.0,
        "high_voltage": 7.0,
        "extra_high_voltage": 10.0,
    }

    INSPECTION_INTERVALS: dict[str, int] = {
        "good": 12,
        "fair": 6,
        "poor": 3,
        "critical": 1,
    }

    def __init__(self, profile: Optional[PowerlineProfile] = None) -> None:
        self.profile = profile

    def assess_condition(self, severity_counts: dict[SeverityLevel, int]) -> str:
        """Assess overall powerline corridor condition."""
        if severity_counts.get(SeverityLevel.CRITICAL, 0) > 0:
            return "critical"
        if severity_counts.get(SeverityLevel.SEVERE, 0) > 0:
            return "poor"
        if severity_counts.get(SeverityLevel.MODERATE, 0) > 2:
            return "poor"
        if severity_counts.get(SeverityLevel.MODERATE, 0) > 0:
            return "fair"
        return "good"

    def get_inspection_interval(self, condition: str) -> int:
        """Get recommended inspection interval in months."""
        return self.INSPECTION_INTERVALS.get(condition, 12)

    def get_voltage_class(self, voltage_kv: float) -> str:
        """Classify voltage level."""
        if voltage_kv < 1:
            return "low_voltage"
        if voltage_kv < 69:
            return "medium_voltage"
        if voltage_kv < 345:
            return "high_voltage"
        return "extra_high_voltage"

    def get_required_clearance(self, voltage_kv: float) -> float:
        """Get required vegetation clearance in meters for a voltage level."""
        voltage_class = self.get_voltage_class(voltage_kv)
        return self.VEGETATION_CLEARANCE[voltage_class]

    def get_component_recommendations(
        self, component: str, defect_type: DefectType, severity: SeverityLevel
    ) -> str:
        """Generate maintenance recommendation for powerline defects.

        Args:
            component: conductor, tower, insulator, foundation
            defect_type: The detected defect type.
            severity: Severity of the defect.
        """
        if component == "conductor":
            if defect_type == DefectType.CORROSION:
                if severity in (SeverityLevel.MINOR, SeverityLevel.MODERATE):
                    return "Monitor strand corrosion; schedule replacement within maintenance cycle."
                return "Replace conductor section; risk of strand failure."
            if defect_type == DefectType.DEFORMATION:
                if severity in (SeverityLevel.MINOR, SeverityLevel.MODERATE):
                    return "Re-sag conductor if necessary."
                return "Replace deformed conductor section immediately."

        if component == "tower":
            if defect_type == DefectType.CORROSION:
                if severity in (SeverityLevel.MINOR, SeverityLevel.MODERATE):
                    return "Spot-paint corroded members."
                return "Section loss assessment; reinforce or replace tower members."
            if defect_type == DefectType.DEFORMATION:
                return "Structural assessment of tower alignment required."

        if component == "insulator":
            if defect_type == DefectType.CRACK:
                if severity in (SeverityLevel.MINOR, SeverityLevel.MODERATE):
                    return "Schedule insulator replacement at next outage."
                return "Replace cracked insulator urgently; flashover risk."

        if defect_type == DefectType.VEGETATION_GROWTH:
            if severity in (SeverityLevel.MINOR, SeverityLevel.MODERATE):
                return "Schedule vegetation trimming within clearance zone."
            return "Immediate vegetation clearing required; outage risk."

        return "Consult powerline engineer for assessment."

    def generate_default_profile(self, corridor_id: str, name: str) -> PowerlineProfile:
        """Create a default powerline corridor profile."""
        towers = [
            TowerProfile(tower_id=f"T-{i:03d}", height_m=35.0, tower_type="lattice")
            for i in range(1, 6)
        ]
        spans = [
            PowerlineSpan(
                span_id=f"S-{i:03d}",
                start_tower=f"T-{i:03d}",
                end_tower=f"T-{i+1:03d}",
                length_m=300.0,
                voltage_kv=138.0,
            )
            for i in range(1, 5)
        ]
        return PowerlineProfile(
            corridor_id=corridor_id,
            name=name,
            voltage_kv=138.0,
            total_length_km=1.2,
            towers=towers,
            spans=spans,
        )
