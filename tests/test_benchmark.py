"""Benchmark tests for Skyeye."""
import time, pytest
from src.core import Skyeye

def test_1000_ops_under_1s():
    c = Skyeye()
    start = time.time()
    for i in range(1000):
        c.analyze(i=i)
    elapsed = time.time() - start
    assert elapsed < 1.0, f"1000 ops took {elapsed:.2f}s"
    assert c.get_stats()["ops"] == 1000

def test_accuracy_at_scale():
    c = Skyeye()
    for i in range(500):
        r = c.analyze(i=i)
        assert r["ok"] is True
        assert r["n"] == i + 1

def test_reset_is_instant():
    c = Skyeye()
    for _ in range(100): c.analyze()
    start = time.time()
    c.reset()
    elapsed = time.time() - start
    assert elapsed < 0.01
    assert c.get_stats()["ops"] == 0

def test_memory_stable():
    """Ensure no memory leaks after reset."""
    c = Skyeye()
    for _ in range(1000): c.analyze(data="x" * 100)
    c.reset()
    assert c.get_stats()["ops"] == 0
    assert c.get_stats()["log_size"] == 0
