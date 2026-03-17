"""Bridge inspection standards and protocols."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from skyeye.models import DefectType, GeoCoordinate, InfrastructureType, SeverityLevel


class BridgeComponent(BaseModel):
    """A structural component of a bridge."""

    name: str
    component_type: str  # deck, pier, abutment, railing, bearing, joint
    material: str  # concrete, steel, timber, masonry
    critical: bool = Field(default=False, description="Whether component is load-bearing")


class BridgeProfile(BaseModel):
    """Profile of a bridge for inspection planning."""

    bridge_id: str
    name: str
    location: Optional[GeoCoordinate] = None
    span_length_m: float = Field(gt=0)
    deck_width_m: float = Field(gt=0)
    num_spans: int = Field(default=1, ge=1)
    bridge_type: str = Field(default="beam", description="beam, arch, suspension, cable-stayed, truss")
    components: list[BridgeComponent] = Field(default_factory=list)
    year_built: Optional[int] = None


class BridgeInspection:
    """Bridge-specific inspection standards and defect assessment.

    Implements inspection protocols aligned with common bridge
    inspection standards, including component-specific severity
    thresholds and recommended inspection intervals.
    """

    INFRASTRUCTURE_TYPE = InfrastructureType.BRIDGE

    # Defect types relevant to bridge inspection, ordered by typical concern
    RELEVANT_DEFECTS: list[DefectType] = [
        DefectType.CRACK,
        DefectType.CORROSION,
        DefectType.SPALLING,
        DefectType.DEFORMATION,
        DefectType.VEGETATION_GROWTH,
    ]

    # Severity thresholds for crack width in mm
    CRACK_THRESHOLDS: dict[SeverityLevel, float] = {
        SeverityLevel.MINOR: 0.2,
        SeverityLevel.MODERATE: 0.5,
        SeverityLevel.SEVERE: 1.0,
        SeverityLevel.CRITICAL: 2.0,
    }

    # Recommended inspection intervals in months by condition
    INSPECTION_INTERVALS: dict[str, int] = {
        "good": 24,
        "fair": 12,
        "poor": 6,
        "critical": 1,
    }

    COMPONENT_TYPES = ["deck", "pier", "abutment", "railing", "bearing", "joint"]

    def __init__(self, profile: Optional[BridgeProfile] = None) -> None:
        self.profile = profile

    def assess_condition(self, severity_counts: dict[SeverityLevel, int]) -> str:
        """Assess overall bridge condition based on defect severity distribution.

        Args:
            severity_counts: Count of defects per severity level.

        Returns:
            Condition rating: "good", "fair", "poor", or "critical".
        """
        if severity_counts.get(SeverityLevel.CRITICAL, 0) > 0:
            return "critical"
        if severity_counts.get(SeverityLevel.SEVERE, 0) > 2:
            return "critical"
        if severity_counts.get(SeverityLevel.SEVERE, 0) > 0:
            return "poor"
        if severity_counts.get(SeverityLevel.MODERATE, 0) > 3:
            return "poor"
        if severity_counts.get(SeverityLevel.MODERATE, 0) > 0:
            return "fair"
        return "good"

    def get_inspection_interval(self, condition: str) -> int:
        """Get recommended inspection interval in months."""
        return self.INSPECTION_INTERVALS.get(condition, 12)

    def get_component_recommendations(
        self, component_type: str, defect_type: DefectType, severity: SeverityLevel
    ) -> str:
        """Generate a maintenance recommendation for a component defect.

        Args:
            component_type: Type of bridge component.
            defect_type: The detected defect type.
            severity: Severity of the defect.

        Returns:
            Recommendation string.
        """
        recs = {
            (DefectType.CRACK, SeverityLevel.MINOR): "Monitor crack; re-inspect in 12 months.",
            (DefectType.CRACK, SeverityLevel.MODERATE): "Seal crack with epoxy injection.",
            (DefectType.CRACK, SeverityLevel.SEVERE): "Structural assessment required; schedule repair.",
            (DefectType.CRACK, SeverityLevel.CRITICAL): "Immediate load restriction; emergency repair needed.",
            (DefectType.CORROSION, SeverityLevel.MINOR): "Clean and apply protective coating.",
            (DefectType.CORROSION, SeverityLevel.MODERATE): "Remove corrosion and repaint with anticorrosive.",
            (DefectType.CORROSION, SeverityLevel.SEVERE): "Assess section loss; reinforce or replace member.",
            (DefectType.CORROSION, SeverityLevel.CRITICAL): "Emergency structural evaluation; possible closure.",
            (DefectType.SPALLING, SeverityLevel.MINOR): "Patch spalled area with repair mortar.",
            (DefectType.SPALLING, SeverityLevel.MODERATE): "Remove loose concrete; apply overlay repair.",
            (DefectType.SPALLING, SeverityLevel.SEVERE): "Rebar exposure likely; full section repair needed.",
            (DefectType.SPALLING, SeverityLevel.CRITICAL): "Major structural repair; restrict loading.",
            (DefectType.DEFORMATION, SeverityLevel.MINOR): "Document and monitor for progression.",
            (DefectType.DEFORMATION, SeverityLevel.MODERATE): "Engineering review of alignment.",
            (DefectType.DEFORMATION, SeverityLevel.SEVERE): "Load testing and structural analysis required.",
            (DefectType.DEFORMATION, SeverityLevel.CRITICAL): "Possible imminent failure; close and assess.",
            (DefectType.VEGETATION_GROWTH, SeverityLevel.MINOR): "Clear vegetation during routine maintenance.",
            (DefectType.VEGETATION_GROWTH, SeverityLevel.MODERATE): "Remove vegetation; inspect for root damage.",
            (DefectType.VEGETATION_GROWTH, SeverityLevel.SEVERE): "Extensive root intrusion; concrete repair needed.",
            (DefectType.VEGETATION_GROWTH, SeverityLevel.CRITICAL): "Vegetation compromising structure; remediate urgently.",
        }
        base = recs.get((defect_type, severity), "Consult structural engineer.")
        if component_type in ("pier", "abutment", "bearing") and severity in (
            SeverityLevel.SEVERE,
            SeverityLevel.CRITICAL,
        ):
            base += " [LOAD-BEARING COMPONENT - ELEVATED PRIORITY]"
        return base

    def generate_default_profile(self, bridge_id: str, name: str) -> BridgeProfile:
        """Create a default bridge profile with standard components."""
        components = [
            BridgeComponent(name="Main Deck", component_type="deck", material="concrete", critical=True),
            BridgeComponent(name="Pier 1", component_type="pier", material="concrete", critical=True),
            BridgeComponent(name="Abutment North", component_type="abutment", material="concrete", critical=True),
            BridgeComponent(name="Abutment South", component_type="abutment", material="concrete", critical=True),
            BridgeComponent(name="Railing East", component_type="railing", material="steel", critical=False),
            BridgeComponent(name="Railing West", component_type="railing", material="steel", critical=False),
            BridgeComponent(name="Expansion Joint 1", component_type="joint", material="steel", critical=False),
        ]
        return BridgeProfile(
            bridge_id=bridge_id,
            name=name,
            span_length_m=50.0,
            deck_width_m=12.0,
            num_spans=2,
            bridge_type="beam",
            components=components,
        )
