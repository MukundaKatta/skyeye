"""Integration tests for Skyeye."""
from src.core import Skyeye

class TestSkyeye:
    def setup_method(self):
        self.c = Skyeye()
    def test_10_ops(self):
        for i in range(10): self.c.analyze(i=i)
        assert self.c.get_stats()["ops"] == 10
    def test_service_name(self):
        assert self.c.analyze()["service"] == "skyeye"
    def test_different_inputs(self):
        self.c.analyze(type="a"); self.c.analyze(type="b")
        assert self.c.get_stats()["ops"] == 2
    def test_config(self):
        c = Skyeye(config={"debug": True})
        assert c.config["debug"] is True
    def test_empty_call(self):
        assert self.c.analyze()["ok"] is True
    def test_large_batch(self):
        for _ in range(100): self.c.analyze()
        assert self.c.get_stats()["ops"] == 100
