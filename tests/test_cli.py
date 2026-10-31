import argparse
from unittest.mock import patch

from input_latency_bench import cli


def test_build_parser_commands():
    p = cli.build_parser()
    for cmd in ("timer", "keypress", "report", "doctor"):
        ns = p.parse_args([cmd])
        assert ns.command == cmd


def test_cmd_doctor():
    with patch("input_latency_bench.doctor.run_doctor", return_value=[]):
        args = cli.build_parser().parse_args(["doctor"])
        assert cli.cmd_doctor(args) == 0


def test_cmd_report():
    with patch("input_latency_bench.report.run_report", return_value=[]):
        args = cli.build_parser().parse_args(["report", "--json"])
        assert args.json is True
        assert cli.cmd_report(args) == 0
