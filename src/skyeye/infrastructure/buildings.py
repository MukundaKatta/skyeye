"""Building inspection standards and protocols."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from skyeye.models import DefectType, GeoCoordinate, InfrastructureType, SeverityLevel


class BuildingFacade(BaseModel):
    """A facade or face of a building to inspect."""

    name: str
    orientation: str  # north, south, east, west
    width_m: float = Field(gt=0)
    height_m: float = Field(gt=0)
    material: str = Field(default="concrete")  # concrete, brick, glass, cladding


class BuildingProfile(BaseModel):
    """Profile of a building for inspection planning."""

    building_id: str
    name: str
    location: Optional[GeoCoordinate] = None
    num_floors: int = Field(ge=1)
    height_m: float = Field(gt=0)
    facades: list[BuildingFacade] = Field(default_factory=list)
    year_built: Optional[int] = None
    building_use: str = Field(default="commercial")


class BuildingInspection:
    """Building-specific inspection standards and defect assessment.

    Covers facade inspection, structural element assessment, and
    building envelope integrity evaluation.
    """

    INFRASTRUCTURE_TYPE = InfrastructureType.BUILDING

    RELEVANT_DEFECTS: list[DefectType] = [
        DefectType.CRACK,
        DefectType.CORROSION,
        DefectType.SPALLING,
        DefectType.DEFORMATION,
        DefectType.VEGETATION_GROWTH,
    ]

    INSPECTION_INTERVALS: dict[str, int] = {
        "good": 36,
        "fair": 18,
        "poor": 6,
        "critical": 1,
    }

    FACADE_MATERIALS = ["concrete", "brick", "glass", "cladding", "stone", "stucco"]

    def __init__(self, profile: Optional[BuildingProfile] = None) -> None:
        self.profile = profile

    def assess_condition(self, severity_counts: dict[SeverityLevel, int]) -> str:
        """Assess overall building facade condition."""
        if severity_counts.get(SeverityLevel.CRITICAL, 0) > 0:
            return "critical"
        if severity_counts.get(SeverityLevel.SEVERE, 0) > 1:
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
        return self.INSPECTION_INTERVALS.get(condition, 18)

    def get_facade_recommendations(
        self, facade_material: str, defect_type: DefectType, severity: SeverityLevel
    ) -> str:
        """Generate maintenance recommendation for facade defects."""
        if defect_type == DefectType.CRACK:
            if severity == SeverityLevel.MINOR:
                return "Fill hairline crack with appropriate sealant."
            if severity == SeverityLevel.MODERATE:
                return "Route and seal crack; check for water ingress."
            if severity == SeverityLevel.SEVERE:
                return "Structural crack assessment; repair with injection grouting."
            return "Evacuate if necessary; immediate structural evaluation."

        if defect_type == DefectType.SPALLING:
            if severity in (SeverityLevel.MINOR, SeverityLevel.MODERATE):
                return "Patch repair with compatible material."
            if severity == SeverityLevel.SEVERE:
                return "Section repair; check rebar condition."
            return "Falling debris hazard; install safety barriers and repair."

        if defect_type == DefectType.CORROSION:
            if severity in (SeverityLevel.MINOR, SeverityLevel.MODERATE):
                return "Clean, treat, and apply protective coating."
            return "Replace corroded elements; assess structural impact."

        if defect_type == DefectType.DEFORMATION:
            if severity in (SeverityLevel.MINOR, SeverityLevel.MODERATE):
                return "Monitor deformation with survey markers."
            return "Structural engineer assessment required immediately."

        if defect_type == DefectType.VEGETATION_GROWTH:
            if severity in (SeverityLevel.MINOR, SeverityLevel.MODERATE):
                return "Remove vegetation; seal entry points."
            return "Extensive vegetation removal; repair water barrier."

        return "Consult building engineer."

    def calculate_facade_area(self) -> float:
        """Total facade area in square meters for the building profile."""
        if not self.profile:
            return 0.0
        return sum(f.width_m * f.height_m for f in self.profile.facades)

    def generate_default_profile(self, building_id: str, name: str) -> BuildingProfile:
        """Create a default building profile with four facades."""
        facades = [
            BuildingFacade(name="North Facade", orientation="north", width_m=30.0, height_m=20.0),
            BuildingFacade(name="South Facade", orientation="south", width_m=30.0, height_m=20.0),
            BuildingFacade(name="East Facade", orientation="east", width_m=20.0, height_m=20.0),
            BuildingFacade(name="West Facade", orientation="west", width_m=20.0, height_m=20.0),
        ]
        return BuildingProfile(
            building_id=building_id,
            name=name,
            num_floors=5,
            height_m=20.0,
            facades=facades,
            building_use="commercial",
        )
