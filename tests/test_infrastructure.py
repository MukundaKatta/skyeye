"""Tests for infrastructure inspection modules."""

import pytest

from skyeye.infrastructure.bridges import BridgeInspection
from skyeye.infrastructure.buildings import BuildingInspection
from skyeye.infrastructure.powerlines import PowerlineInspection
from skyeye.models import DefectType, SeverityLevel


class TestBridgeInspection:
    def test_assess_good(self):
        bi = BridgeInspection()
        result = bi.assess_condition({SeverityLevel.MINOR: 3})
        assert result == "good"

    def test_assess_fair(self):
        bi = BridgeInspection()
        result = bi.assess_condition({SeverityLevel.MODERATE: 1})
        assert result == "fair"

    def test_assess_poor(self):
        bi = BridgeInspection()
        result = bi.assess_condition({SeverityLevel.SEVERE: 1})
        assert result == "poor"

    def test_assess_critical(self):
        bi = BridgeInspection()
        result = bi.assess_condition({SeverityLevel.CRITICAL: 1})
        assert result == "critical"

    def test_assess_critical_many_severe(self):
        bi = BridgeInspection()
        result = bi.assess_condition({SeverityLevel.SEVERE: 5})
        assert result == "critical"

    def test_inspection_interval(self):
        bi = BridgeInspection()
        assert bi.get_inspection_interval("good") == 24
        assert bi.get_inspection_interval("critical") == 1

    def test_component_recommendation(self):
        bi = BridgeInspection()
        rec = bi.get_component_recommendations("deck", DefectType.CRACK, SeverityLevel.MINOR)
        assert "Monitor" in rec or "monitor" in rec.lower()

    def test_critical_load_bearing_flag(self):
        bi = BridgeInspection()
        rec = bi.get_component_recommendations("pier", DefectType.CRACK, SeverityLevel.CRITICAL)
        assert "LOAD-BEARING" in rec

    def test_generate_default_profile(self):
        bi = BridgeInspection()
        profile = bi.generate_default_profile("BR-001", "Test Bridge")
        assert profile.bridge_id == "BR-001"
        assert len(profile.components) > 0


class TestBuildingInspection:
    def test_assess_condition(self):
        bi = BuildingInspection()
        assert bi.assess_condition({SeverityLevel.MINOR: 5}) == "good"
        assert bi.assess_condition({SeverityLevel.CRITICAL: 1}) == "critical"

    def test_facade_recommendations(self):
        bi = BuildingInspection()
        rec = bi.get_facade_recommendations("concrete", DefectType.CRACK, SeverityLevel.MINOR)
        assert len(rec) > 0

    def test_calculate_facade_area_no_profile(self):
        bi = BuildingInspection()
        assert bi.calculate_facade_area() == 0.0

    def test_generate_default_profile(self):
        bi = BuildingInspection()
        profile = bi.generate_default_profile("BLD-001", "Test Building")
        assert len(profile.facades) == 4
        assert bi.calculate_facade_area() == 0.0  # profile not assigned to instance

    def test_facade_area_with_profile(self):
        bi = BuildingInspection()
        profile = bi.generate_default_profile("BLD-001", "Office")
        bi.profile = profile
        area = bi.calculate_facade_area()
        assert area > 0


class TestPowerlineInspection:
    def test_assess_condition(self):
        pi = PowerlineInspection()
        assert pi.assess_condition({SeverityLevel.MINOR: 10}) == "good"
        assert pi.assess_condition({SeverityLevel.CRITICAL: 1}) == "critical"

    def test_voltage_class(self):
        pi = PowerlineInspection()
        assert pi.get_voltage_class(0.4) == "low_voltage"
        assert pi.get_voltage_class(33) == "medium_voltage"
        assert pi.get_voltage_class(138) == "high_voltage"
        assert pi.get_voltage_class(500) == "extra_high_voltage"

    def test_required_clearance(self):
        pi = PowerlineInspection()
        assert pi.get_required_clearance(0.4) == 3.0
        assert pi.get_required_clearance(500) == 10.0

    def test_component_recommendations(self):
        pi = PowerlineInspection()
        rec = pi.get_component_recommendations("conductor", DefectType.CORROSION, SeverityLevel.MINOR)
        assert len(rec) > 0

    def test_vegetation_recommendation(self):
        pi = PowerlineInspection()
        rec = pi.get_component_recommendations("any", DefectType.VEGETATION_GROWTH, SeverityLevel.SEVERE)
        assert "vegetation" in rec.lower() or "clearing" in rec.lower()

    def test_generate_default_profile(self):
        pi = PowerlineInspection()
        profile = pi.generate_default_profile("PL-001", "Test Corridor")
        assert len(profile.towers) == 5
        assert len(profile.spans) == 4
