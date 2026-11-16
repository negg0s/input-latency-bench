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


def iqr(values):
    """Compute the interquartile range (IQR = Q75 - Q25).

    Returns 0.0 when values is empty or contains fewer than 2 valid samples.
    """
    clean = [float(v) for v in values if _is_number(v)]
    if len(clean) < 2:
        return 0.0
    return percentile(clean, 75) - percentile(clean, 25)


def interquartile_range(values):
    return iqr(values)


def find_outliers(values, factor=1.5):
    """Find outlier values using Tukey fences (Q25 - factor*IQR, Q75 + factor*IQR).

    Returns an empty list when fewer than 4 valid samples are provided,
    because small sample sizes (such as 1 or 2 samples) cannot reliably
    identify outliers.
    """
    clean = [float(v) for v in values if _is_number(v)]
    if len(clean) < 4:
        return []
    spread = iqr(clean)
    if spread == 0.0:
        return []
    q25 = percentile(clean, 25)
    q75 = percentile(clean, 75)
    lower = q25 - factor * spread
    upper = q75 + factor * spread
    return [v for v in clean if v < lower or v > upper]


def detect_outliers(values, factor=1.5):
    return find_outliers(values, factor=factor)


def summarize(values):
    values = [float(v) for v in values if _is_number(v)]
    if not values:
        return {
            "count": 0,
            "min": None,
            "median": None,
            "p95": None,
            "p99": None,
            "max": None,
            "mean": None,
            "stddev": None,
            "iqr": None,
        }
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return {
        "count": len(values),
        "min": min(values),
        "median": percentile(values, 50),
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
        "max": max(values),
        "mean": mean,
        "stddev": math.sqrt(variance),
        "iqr": iqr(values),
    }


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


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


def run_stats(path, field=None, json_output=False, csv_output=False, printer=print):
    values = collect_values(path, field=field)
    result = summarize(values)
    if json_output:
        printer(json.dumps(result, indent=2))
    elif csv_output:
        headers = ["count", "min", "median", "p95", "p99", "max", "mean", "stddev"]
        printer(",".join(headers))
        row = [f"{result[h]:.3f}" if isinstance(result[h], float) else str(result[h] or "") for h in headers]
        printer(",".join(row))
    else:
        printer(f"file: {Path(path)}")
        printer(f"samples: {result['count']}")
        for key in ("min", "median", "p95", "p99", "max", "mean", "stddev"):
            value = result[key]
            printer(f"{key}: {value:.3f}" if value is not None else f"{key}: n/a")
    return result
