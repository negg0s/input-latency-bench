"""Reporting of stored JSONL benchmark results."""

import json
import math

from . import storage
from .stats import summarize


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


def _field_value(record, field):
    value = record
    for part in field.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return float(value)


def run_compare(path, field="hold_ms", printer=print):
    """Summarize a numeric field from each labeled run in a JSONL file."""
    groups = {}
    for record in storage.load_records(path):
        if not isinstance(record, dict):
            continue
        label = record.get("label")
        if not isinstance(label, str) or not label.strip():
            continue
        value = _field_value(record, field)
        if value is not None:
            groups.setdefault(label, []).append(value)

    if len(groups) < 2:
        raise ValueError("comparison needs at least two labeled runs with numeric values")

    summaries = {label: summarize(values) for label, values in groups.items()}
    printer(f"Comparison: {field}")
    first_label = next(iter(summaries))
    first_median = summaries[first_label]["median"]
    for label, result in summaries.items():
        printer(
            f"{label}: samples={result['count']} median={result['median']:.3f} "
            f"p95={result['p95']:.3f} mean={result['mean']:.3f}"
        )
        if label != first_label:
            difference = result["median"] - first_median
            percent = "n/a" if first_median == 0 else f"{difference / first_median * 100:+.1f}%"
            printer(
                f"  {label} vs {first_label}: median difference "
                f"{difference:+.3f} ({percent})"
            )
    printer("Descriptive comparison only. This does not measure end-to-end input latency.")
    return summaries
