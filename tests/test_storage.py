import json

from input_latency_bench import storage


def test_append_writes_one_line_per_record(tmp_path):
    path = tmp_path / "results.jsonl"
    storage.append_result({"command": "timer", "x": 1}, path=path)
    storage.append_result({"command": "keypress", "y": 2}, path=path)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["command"] == "timer"
    assert first["x"] == 1
    assert first["timestamp"].endswith("Z")


def test_append_keeps_existing_timestamp(tmp_path):
    path = tmp_path / "results.jsonl"
    storage.append_result({"timestamp": "2020-01-01T00:00:00.000Z", "v": 1}, path=path)
    record = storage.load_records(path)[0]
    assert record["timestamp"] == "2020-01-01T00:00:00.000Z"


def test_load_missing_returns_empty(tmp_path):
    assert storage.load_records(tmp_path / "nope.jsonl") == []


def test_load_skips_malformed_lines(tmp_path):
    path = tmp_path / "results.jsonl"
    path.write_text('{"a": 1}\nnot json\n\n{"b": 2}\n', encoding="utf-8")
    assert storage.load_records(path) == [{"a": 1}, {"b": 2}]
    assert storage.load_results(path) == [{"a": 1}, {"b": 2}]


def test_default_path_uses_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("INPUT_LATENCY_BENCH_HOME", str(tmp_path))
    assert storage.default_path() == tmp_path / "results.jsonl"


def test_clear(tmp_path):
    path = tmp_path / "results.jsonl"
    storage.append_result({"a": 1}, path=path)
    storage.clear_results(path=path)
    assert not path.exists()
