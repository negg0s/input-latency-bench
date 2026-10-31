"""Numeric summaries and JSONL sample loading."""

import json
import math
from pathlib import Path

from . import storage

DEFAULT_FIELDS = ("value", "hold_ms", "latency_ms", "ms", "duration_ms")


def percentile(values, p):
    if not values:
        raise ValueError("values must not be empty")
    if p < 0 or p > 100:
        raise ValueError("p must be between 0 and 100")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * p / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def summarize(values):
    values = [float(v) for v in values]
    if not values:
        return {
            "count": 0,
            "min": None,
            "median": None,
            "p95": None,
            "max": None,
            "mean": None,
        }
    return {
        "count": len(values),
        "min": min(values),
        "median": percentile(values, 50),
        "p95": percentile(values, 95),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _lookup(record, field):
    current = record
    for part in field.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def collect_values(path, field=None):
    records = storage.load_records(path)
    values = []
    for record in records:
        if _is_number(record):
            if field is None:
                values.append(float(record))
            continue
        if not isinstance(record, dict):
            continue
        if field:
            value = _lookup(record, field)
        else:
            value = None
            for name in DEFAULT_FIELDS:
                if name in record:
                    value = record[name]
                    break
        if _is_number(value):
            values.append(float(value))
    return values


def run_stats(path, field=None, json_output=False, printer=print):
    values = collect_values(path, field=field)
    result = summarize(values)
    if json_output:
        printer(json.dumps(result, indent=2))
    else:
        printer(f"file: {Path(path)}")
        printer(f"samples: {result['count']}")
        for key in ("min", "median", "p95", "max", "mean"):
            value = result[key]
            printer(f"{key}: {value:.3f}" if value is not None else f"{key}: n/a")
    return result
