"""Command-line interface."""

import argparse
import json
import sys

from . import doctor, keypress, report, stats, storage, timer


def _print_timer(result):
    print(f"frequency: {result['frequency']} Hz")
    print(f"tick: {result['tick_ns']:.3f} ns")
    print(f"samples: {result['samples']}")
    print(f"zero deltas: {result['zero_delta_count']}")
    for label in ("resolution", "overhead"):
        summary = result[f"{label}_ns"]
        values = " ".join(
            f"{key}={summary[key]:.3f}"
            for key in ("min", "median", "p95", "max", "mean")
            if summary[key] is not None
        )
        print(f"{label} (ns): {values}")


def cmd_timer(args):
    result = timer.measure_timer(samples=args.samples)
    out = {"command": "timer", **result}
    if args.label:
        out["label"] = args.label
    storage.append_result(out, path=args.output)
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        _print_timer(out)
    return 0


def cmd_keypress(args):
    result = keypress.measure_keypress(samples=args.samples)
    session = storage.utc_now()
    for event in result["events"]:
        storage.append_result(
            {
                "command": "keypress",
                "session": session,
                **({"label": args.label} if args.label else {}),
                "frequency": result["frequency"],
                **event,
            },
            path=args.output,
        )

    print("summary:")
    print(f"  count: {result['count']}")
    for label in ("hold_ms", "interval_ms"):
        summary = result[label]
        for key in ("min", "median", "p95", "max", "mean"):
            value = summary[key]
            if value is not None:
                print(f"  {label} {key}: {value:.3f}")
    if result["events"]:
        print(f"  saved to: {args.output or storage.default_path()}")
    return 0


def cmd_stats(args):
    stats.run_stats(args.file, field=args.field, json_output=args.json)
    return 0


def cmd_report(args):
    report.run_report(json_output=args.json, path=args.path)
    return 0


def cmd_compare(args):
    try:
        report.run_compare(args.file, field=args.field)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def cmd_doctor(args):
    if getattr(args, "json", False):
        checks = doctor.run_doctor(printer=lambda _: None)
        payload = {
            "checks": [{"name": name, "ok": ok, "detail": detail} for name, ok, detail in checks],
            "passed": sum(1 for _, ok, _ in checks if ok),
            "total": len(checks),
        }
        print(json.dumps(payload, indent=2))
        return 0 if all(ok for _, ok, _ in checks) else 1
    checks = doctor.run_doctor()
    return 0 if all(ok for _, ok, _ in checks) else 1


def build_parser():
    parser = argparse.ArgumentParser(
        prog="input-latency-bench",
        description="Software-side Windows timer and keypress timing.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_timer = sub.add_parser("timer", help="Measure QPC frequency, resolution, and overhead")
    p_timer.add_argument("--samples", type=int, default=1000)
    p_timer.add_argument("--label", type=str, help="Name this run for later comparison")
    p_timer.add_argument("--output", type=str, default=None, help="JSONL output path")
    p_timer.add_argument("--json", action="store_true", help="Print the result as JSON")
    p_timer.set_defaults(func=cmd_timer)

    p_key = sub.add_parser("keypress", help="Measure key hold and inter-key timing")
    p_key.add_argument("--samples", type=int, default=5)
    p_key.add_argument("--label", type=str, help="Name this run for later comparison")
    p_key.add_argument("--output", type=str, default=None, help="JSONL output path")
    p_key.set_defaults(func=cmd_keypress)

    p_stats = sub.add_parser("stats", help="Summarize numeric values in a JSONL file")
    p_stats.add_argument("file", help="JSONL file with numbers or records")
    p_stats.add_argument(
        "--field",
        type=str,
        default=None,
        help="Record field to read, supports dot paths (default: value, hold_ms, ...)",
    )
    p_stats.add_argument("--json", action="store_true")
    p_stats.set_defaults(func=cmd_stats)

    p_rep = sub.add_parser("report", help="Show stored JSONL results")
    p_rep.add_argument("--json", action="store_true")
    p_rep.add_argument("--path", type=str, default=None, help="JSONL file to read")
    p_rep.set_defaults(func=cmd_report)

    p_compare = sub.add_parser("compare", help="Compare labeled numeric results")
    p_compare.add_argument("file", help="JSONL file containing labeled runs")
    p_compare.add_argument(
        "--field",
        type=str,
        default="hold_ms",
        help="Numeric field to compare, supports dot paths (default: hold_ms)",
    )
    p_compare.set_defaults(func=cmd_compare)

    p_doc = sub.add_parser("doctor", help="Environment diagnostics")
    p_doc.add_argument("--json", action="store_true", help="Output diagnostics as JSON")
    p_doc.set_defaults(func=cmd_doctor)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
