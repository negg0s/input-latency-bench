"""Reporting of stored JSONL benchmark results."""

import json

from . import storage


def _format_summary(summary):
    if not isinstance(summary, dict):
        return str(summary)
    parts = []
    for key in ("min", "median", "p95", "max", "mean"):
        value = summary.get(key)
        if value is None:
            continue
        parts.append(f"{key}={value:.3f}")
    count = summary.get("count")
    if count is not None:
        parts.append(f"count={count}")
    return " ".join(parts)


def run_report(json_output=False, path=None, printer=print):
    records = storage.load_records(path)
    if json_output:
        printer(json.dumps(records, indent=2))
        return records
    if not records:
        printer("No stored results. Run 'timer' or 'keypress' first.")
        return records

    for index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            printer(f"[{index}] {record}")
            continue
        command = record.get("command", "unknown")
        timestamp = record.get("timestamp", "unknown")
        if command == "timer":
            printer(f"[{index}] timer at {timestamp}")
            printer(f"  frequency: {record.get('frequency')} Hz")
            printer(f"  tick: {record.get('tick_ns', 0):.3f} ns")
            printer(f"  resolution: {_format_summary(record.get('resolution_ns'))}")
            printer(f"  overhead: {_format_summary(record.get('overhead_ns'))}")
            printer(f"  zero deltas: {record.get('zero_delta_count')}")
        elif command == "keypress":
            interval = record.get("interval_ms")
            interval_text = "n/a" if interval is None else f"{interval:.3f} ms"
            printer(
                f"[{index}] keypress trial {record.get('trial')} at {timestamp} "
                f"hold={record.get('hold_ms', 0):.3f} ms interval={interval_text}"
            )
        else:
            printer(f"[{index}] {command} at {timestamp}")
            for key, value in record.items():
                if key in ("command", "timestamp"):
                    continue
                printer(f"  {key}: {value}")
    return records
