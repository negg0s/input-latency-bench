from unittest.mock import patch

from input_latency_bench import cli


def test_build_parser_commands():
    parser = cli.build_parser()
    for command in ("timer", "keypress", "stats", "report", "doctor"):
        args = parser.parse_args([command]) if command != "stats" else parser.parse_args(
            [command, "samples.jsonl"]
        )
        assert args.command == command


def test_cmd_timer_saves_jsonl(tmp_path):
    output = tmp_path / "timer.jsonl"
    fake = {
        "frequency": 10_000_000,
        "samples": 2,
        "tick_ns": 100.0,
        "zero_delta_count": 0,
        "resolution_ns": {"count": 2, "min": 100.0, "median": 100.0, "p95": 100.0, "max": 100.0, "mean": 100.0},
        "overhead_ns": {"count": 2, "min": 100.0, "median": 100.0, "p95": 100.0, "max": 100.0, "mean": 100.0},
        "min_delta_ticks": 1,
        "max_delta_ticks": 1,
    }
    with patch("input_latency_bench.cli.timer.measure_timer", return_value=fake):
        args = cli.build_parser().parse_args(["timer", "--output", str(output)])
        assert cli.cmd_timer(args) == 0
    assert output.exists()


def test_cmd_keypress_saves_events(tmp_path):
    output = tmp_path / "keys.jsonl"
    fake = {
        "frequency": 1_000_000,
        "count": 1,
        "hold_ms": {"count": 1, "min": 10.0, "median": 10.0, "p95": 10.0, "max": 10.0, "mean": 10.0},
        "interval_ms": {"count": 0, "min": None, "median": None, "p95": None, "max": None, "mean": None},
        "events": [{"trial": 1, "hold_ms": 10.0, "interval_ms": None}],
    }
    with patch("input_latency_bench.cli.keypress.measure_keypress", return_value=fake):
        args = cli.build_parser().parse_args(["keypress", "--output", str(output)])
        assert cli.cmd_keypress(args) == 0
    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert '"hold_ms":10.0' in lines[0]


def test_cmd_stats(tmp_path):
    path = tmp_path / "samples.jsonl"
    path.write_text("1\n2\n3\n", encoding="utf-8")
    args = cli.build_parser().parse_args(["stats", str(path), "--json"])
    assert cli.cmd_stats(args) == 0


def test_cmd_report(tmp_path):
    path = tmp_path / "r.jsonl"
    path.write_text('{"command": "timer"}\n', encoding="utf-8")
    args = cli.build_parser().parse_args(["report", "--path", str(path), "--json"])
    assert cli.cmd_report(args) == 0


def test_cmd_doctor():
    with patch("input_latency_bench.doctor.run_doctor", return_value=[]):
        args = cli.build_parser().parse_args(["doctor"])
        assert cli.cmd_doctor(args) == 0
