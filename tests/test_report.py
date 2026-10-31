import json

from input_latency_bench import report, storage


def test_report_empty(tmp_path):
    out = []
    report.run_report(path=tmp_path / "r.jsonl", printer=out.append)
    assert any("No stored results" in line for line in out)


def test_report_json_returns_records(tmp_path):
    path = tmp_path / "r.jsonl"
    storage.append_result({"command": "timer", "resolution_ns": {"min": 100.0}}, path=path)
    out = []
    records = report.run_report(json_output=True, path=path, printer=out.append)
    parsed = json.loads("\n".join(out))
    assert isinstance(parsed, list)
    assert parsed[0]["command"] == "timer"
    assert records[0]["resolution_ns"]["min"] == 100.0


def test_report_text_timer(tmp_path):
    path = tmp_path / "r.jsonl"
    storage.append_result(
        {
            "command": "timer",
            "frequency": 10_000_000,
            "tick_ns": 100.0,
            "resolution_ns": {"count": 2, "min": 100.0, "median": 100.0, "p95": 100.0, "max": 100.0},
            "overhead_ns": {"count": 2, "min": 100.0, "median": 100.0, "p95": 100.0, "max": 100.0},
            "zero_delta_count": 0,
        },
        path=path,
    )
    out = []
    report.run_report(path=path, printer=out.append)
    text = "\n".join(out)
    assert "timer" in text
    assert "resolution" in text
    assert "min=100.000" in text


def test_report_text_keypress(tmp_path):
    path = tmp_path / "r.jsonl"
    storage.append_result(
        {"command": "keypress", "trial": 1, "hold_ms": 12.5, "interval_ms": None},
        path=path,
    )
    out = []
    report.run_report(path=path, printer=out.append)
    text = "\n".join(out)
    assert "hold=12.500" in text
    assert "interval=n/a" in text
