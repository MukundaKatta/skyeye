"""Tests for Skyeye."""
from src.core import Skyeye
def test_init(): assert Skyeye().get_stats()["ops"] == 0
def test_op(): c = Skyeye(); c.analyze(x=1); assert c.get_stats()["ops"] == 1
def test_multi(): c = Skyeye(); [c.analyze() for _ in range(5)]; assert c.get_stats()["ops"] == 5
def test_reset(): c = Skyeye(); c.analyze(); c.reset(); assert c.get_stats()["ops"] == 0
def test_service_name(): c = Skyeye(); r = c.analyze(); assert r["service"] == "skyeye"
