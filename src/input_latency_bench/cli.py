"""Command-line interface."""

import argparse
import json

from . import doctor, keypress, report, storage, timer


def _print_timer(result):
    print(f"frequency: {result['frequency']} Hz")
    print(f"samples: {result['samples']}")
    print(f"resolution: {result['resolution_ns']:.2f} ns")
    print(f"overhead: {result['overhead_ns']:.2f} ns/call")
    print(f"zero deltas: {result['zero_delta_count']}")


def cmd_timer(args):
    result = timer.measure_timer(samples=args.samples)
    result = {"command": "timer", **result}
    storage.save_result(result)
    _print_timer(result)
    return 0


def cmd_keypress(args):
    result = keypress.measure_keypress(samples=args.samples)
    out = {"command": "keypress", **result}
    storage.save_result(out)
    print("summary:")
    print(f"  count: {result['count']}")
    if result["count"]:
        print(f"  min: {result['min_ms']:.2f} ms")
        print(f"  max: {result['max_ms']:.2f} ms")
        print(f"  mean: {result['mean_ms']:.2f} ms")
        print(f"  median: {result['median_ms']:.2f} ms")
    return 0


def cmd_report(args):
    report.run_report(json_output=args.json)
    return 0


def cmd_doctor(args):
    doctor.run_doctor()
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="input-latency-bench")
    sub = parser.add_subparsers(dest="command", required=True)

    p_timer = sub.add_parser("timer", help="Measure QPC resolution/overhead")
    p_timer.add_argument("--samples", type=int, default=1000)
    p_timer.set_defaults(func=cmd_timer)

    p_key = sub.add_parser("keypress", help="Interactive keypress latency")
    p_key.add_argument("--samples", type=int, default=5)
    p_key.set_defaults(func=cmd_keypress)

    p_rep = sub.add_parser("report", help="Show stored results")
    p_rep.add_argument("--json", action="store_true")
    p_rep.set_defaults(func=cmd_report)

    p_doc = sub.add_parser("doctor", help="Environment diagnostics")
    p_doc.set_defaults(func=cmd_doctor)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
