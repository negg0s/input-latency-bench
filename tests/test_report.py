import json
from unittest.mock import patch

from input_latency_bench import report, storage


def test_report_empty(tmp_path):
    p = tmp_path / "r.json"
    out = []
    report.run_report(path=p, printer=out.append)
    assert any("No stored results" in s for s in out)


def test_report_json(tmp_path):
    p = tmp_path / "r.json"
    storage.save_result({"command": "timer", "resolution_ns": 100.0}, path=p)
    out = []
    report.run_report(json_output=True, path=p, printer=out.append)
    parsed = json.loads("\n".join(out))
    assert isinstance(parsed, list)
    assert parsed[0]["command"] == "timer"


def test_report_text(tmp_path):
    p = tmp_path / "r.json"
    storage.save_result({"command": "timer", "resolution_ns": 100.0}, path=p)
    out = []
    report.run_report(path=p, printer=out.append)
    text = "\n".join(out)
    assert "timer" in text
    assert "resolution_ns" in text
