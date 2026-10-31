import json
from pathlib import Path

from input_latency_bench import storage


def test_save_and_load(tmp_path):
    p = tmp_path / "results.json"
    storage.save_result({"command": "timer", "x": 1}, path=p)
    storage.save_result({"command": "keypress", "y": 2}, path=p)
    data = storage.load_results(path=p)
    assert len(data) == 2
    assert data[0]["command"] == "timer"
    assert data[1]["y"] == 2


def test_load_missing_returns_empty(tmp_path):
    p = tmp_path / "nope.json"
    assert storage.load_results(path=p) == []


def test_clear(tmp_path):
    p = tmp_path / "results.json"
    storage.save_result({"a": 1}, path=p)
    storage.clear_results(path=p)
    assert not p.exists()
