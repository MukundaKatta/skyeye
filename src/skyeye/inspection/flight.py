"""Flight planning for drone inspection missions."""

from __future__ import annotations

import math
from typing import Optional

from pydantic import BaseModel, Field

from skyeye.models import GeoCoordinate, InfrastructureType, Waypoint


class FlightPlan(BaseModel):
    """A complete drone inspection flight plan.

    Defines waypoints, altitude constraints, camera overlap settings,
    and flight parameters for systematic infrastructure coverage.
    """

    name: str
    infrastructure_type: InfrastructureType
    waypoints: list[Waypoint] = Field(default_factory=list)
    altitude: float = Field(default=30.0, gt=0, description="Default altitude in meters")
    overlap_forward: float = Field(
        default=0.75, ge=0.0, le=1.0, description="Forward image overlap ratio"
    )
    overlap_side: float = Field(
        default=0.60, ge=0.0, le=1.0, description="Side image overlap ratio"
    )
    speed: float = Field(default=5.0, gt=0, description="Flight speed in m/s")
    max_flight_time: float = Field(
        default=25.0, gt=0, description="Max flight time in minutes"
    )
    home_position: Optional[GeoCoordinate] = None

    @property
    def total_waypoints(self) -> int:
        return len(self.waypoints)

    @property
    def estimated_duration_minutes(self) -> float:
        """Estimate flight duration based on waypoint distances and hover times."""
        if len(self.waypoints) < 2:
            return sum(wp.hover_time for wp in self.waypoints) / 60.0

        total_seconds = 0.0
        for i in range(len(self.waypoints) - 1):
            dist = self._haversine(
                self.waypoints[i].coordinate, self.waypoints[i + 1].coordinate
            )
            total_seconds += dist / self.speed
            total_seconds += self.waypoints[i].hover_time
        total_seconds += self.waypoints[-1].hover_time
        return round(total_seconds / 60.0, 2)

    @property
    def capture_count(self) -> int:
        """Number of waypoints configured to capture images."""
        return sum(1 for wp in self.waypoints if wp.capture)

    def add_waypoint(
        self,
        latitude: float,
        longitude: float,
        altitude: Optional[float] = None,
        heading: float = 0.0,
        gimbal_pitch: float = -90.0,
        hover_time: float = 2.0,
        capture: bool = True,
    ) -> Waypoint:
        """Add a waypoint to the flight plan.

        Returns:
            The created Waypoint.
        """
        wp = Waypoint(
            id=len(self.waypoints) + 1,
            coordinate=GeoCoordinate(
                latitude=latitude,
                longitude=longitude,
                altitude=altitude or self.altitude,
            ),
            heading=heading,
            gimbal_pitch=gimbal_pitch,
            hover_time=hover_time,
            capture=capture,
        )
        self.waypoints.append(wp)
        return wp

    def generate_grid_pattern(
        self,
        center: GeoCoordinate,
        width_m: float,
        height_m: float,
        spacing_m: Optional[float] = None,
    ) -> list[Waypoint]:
        """Generate a grid survey pattern centered on a coordinate.

        Args:
            center: Center point of the survey area.
            width_m: Survey width in meters.
            height_m: Survey height in meters.
            spacing_m: Distance between flight lines. Defaults to
                       altitude-based spacing with configured overlap.

        Returns:
            List of generated Waypoint objects.
        """
        if spacing_m is None:
            # Approximate sensor footprint at the given altitude
            fov_h = 2 * self.altitude * math.tan(math.radians(40))
            spacing_m = fov_h * (1 - self.overlap_side)

        rows = max(1, int(height_m / spacing_m))
        cols = max(1, int(width_m / spacing_m))

        generated: list[Waypoint] = []
        for r in range(rows):
            col_range = range(cols) if r % 2 == 0 else range(cols - 1, -1, -1)
            for c in col_range:
                offset_x = (c - cols / 2) * spacing_m
                offset_y = (r - rows / 2) * spacing_m
                lat = center.latitude + (offset_y / 111_320)
                lon = center.longitude + (
                    offset_x / (111_320 * math.cos(math.radians(center.latitude)))
                )
                wp = self.add_waypoint(latitude=lat, longitude=lon)
                generated.append(wp)
        return generated

    @staticmethod
    def _haversine(a: GeoCoordinate, b: GeoCoordinate) -> float:
        """Compute distance in meters between two geographic coordinates."""
        R = 6_371_000
        lat1, lat2 = math.radians(a.latitude), math.radians(b.latitude)
        dlat = lat2 - lat1
        dlon = math.radians(b.longitude - a.longitude)
        h = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        return 2 * R * math.asin(math.sqrt(h))
