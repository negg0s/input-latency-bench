import json

from input_latency_bench import stats


def test_percentile_interpolates():
    assert stats.percentile([1, 2, 3, 4], 50) == 2.5
    assert stats.percentile([1, 2, 3, 4], 95) == 3.85
    assert stats.percentile([7], 95) == 7.0


def test_summarize_known_values():
    result = stats.summarize([1, 2, 3, 4, 5])
    assert result["count"] == 5
    assert result["min"] == 1
    assert result["median"] == 3
    assert result["p95"] == 4.8
    assert result["max"] == 5
    assert result["mean"] == 3


def test_summarize_empty():
    result = stats.summarize([])
    assert result["count"] == 0
    assert result["median"] is None


def test_collect_values_from_jsonl(tmp_path):
    path = tmp_path / "samples.jsonl"
    lines = [
        json.dumps({"command": "keypress", "hold_ms": 10.0}),
        json.dumps({"command": "keypress", "hold_ms": 20.0}),
        json.dumps({"command": "keypress", "interval_ms": 99.0}),
        "not json",
        json.dumps(30.0),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")

    assert stats.collect_values(path) == [10.0, 20.0, 30.0]
    assert stats.collect_values(path, field="interval_ms") == [99.0]


def test_collect_values_dot_path(tmp_path):
    path = tmp_path / "nested.jsonl"
    path.write_text(json.dumps({"result": {"ms": 12.5}}) + "\n", encoding="utf-8")
    assert stats.collect_values(path, field="result.ms") == [12.5]


def test_run_stats_text(tmp_path):
    path = tmp_path / "samples.jsonl"
    path.write_text("1\n2\n3\n4\n", encoding="utf-8")
    out = []
    result = stats.run_stats(path, printer=out.append)
    assert result["count"] == 4
    assert any("median: 2.500" in line for line in out)
