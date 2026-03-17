"""Pydantic data models for SKYEYE domain objects."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DefectType(str, Enum):
    """Categories of infrastructure defects detectable by SKYEYE."""

    CRACK = "crack"
    CORROSION = "corrosion"
    SPALLING = "spalling"
    DEFORMATION = "deformation"
    VEGETATION_GROWTH = "vegetation_growth"


class SeverityLevel(str, Enum):
    """Severity grades for detected defects."""

    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class PriorityLevel(str, Enum):
    """Priority levels for inspection findings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class InfrastructureType(str, Enum):
    """Types of infrastructure that can be inspected."""

    BRIDGE = "bridge"
    BUILDING = "building"
    POWERLINE = "powerline"


class BoundingBox(BaseModel):
    """Bounding box for a detected defect region."""

    x_min: float = Field(ge=0, description="Left edge coordinate")
    y_min: float = Field(ge=0, description="Top edge coordinate")
    x_max: float = Field(ge=0, description="Right edge coordinate")
    y_max: float = Field(ge=0, description="Bottom edge coordinate")

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2


class GeoCoordinate(BaseModel):
    """Geographic coordinate with optional altitude."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    altitude: Optional[float] = Field(default=None, ge=0, description="Altitude in meters")


class Waypoint(BaseModel):
    """A waypoint in an inspection flight plan."""

    id: int
    coordinate: GeoCoordinate
    heading: float = Field(ge=0, lt=360, description="Camera heading in degrees")
    gimbal_pitch: float = Field(default=-90.0, ge=-90, le=0, description="Gimbal pitch angle")
    hover_time: float = Field(default=2.0, ge=0, description="Hover duration in seconds")
    capture: bool = Field(default=True, description="Whether to capture image at this waypoint")


class Detection(BaseModel):
    """A single defect detection result."""

    defect_type: DefectType
    confidence: float = Field(ge=0, le=1)
    bounding_box: BoundingBox
    severity: Optional[SeverityLevel] = None
    description: Optional[str] = None


class SegmentationMask(BaseModel):
    """Metadata for a segmentation mask output."""

    width: int = Field(gt=0)
    height: int = Field(gt=0)
    defect_type: DefectType
    pixel_count: int = Field(ge=0, description="Number of defect pixels")
    coverage_ratio: float = Field(ge=0, le=1, description="Fraction of image covered by defect")


class DefectRecord(BaseModel):
    """Historical record of a defect observation for tracking."""

    defect_id: str
    inspection_date: datetime
    defect_type: DefectType
    severity: SeverityLevel
    location: GeoCoordinate
    bounding_box: BoundingBox
    confidence: float = Field(ge=0, le=1)
    area_pixels: int = Field(ge=0)
    notes: Optional[str] = None


class Finding(BaseModel):
    """A finding in an inspection report."""

    id: str
    defect_type: DefectType
    severity: SeverityLevel
    priority: PriorityLevel
    location_description: str
    recommendation: str
    image_references: list[str] = Field(default_factory=list)
    detection: Optional[Detection] = None


class InspectionMetadata(BaseModel):
    """Metadata for a drone inspection session."""

    inspection_id: str
    infrastructure_type: InfrastructureType
    date: datetime = Field(default_factory=datetime.now)
    inspector: Optional[str] = None
    drone_model: Optional[str] = None
    location: Optional[GeoCoordinate] = None
    weather_conditions: Optional[str] = None
    total_images: int = Field(default=0, ge=0)
    flight_duration_minutes: Optional[float] = Field(default=None, ge=0)
