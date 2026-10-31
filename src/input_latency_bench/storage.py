"""Local result storage as JSON Lines."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def utc_now():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def default_path():
    base = os.environ.get("INPUT_LATENCY_BENCH_HOME")
    if base:
        return Path(base) / "results.jsonl"
    return Path.home() / ".input-latency-bench" / "results.jsonl"


def append_result(result, path=None):
    """Append one record to the JSONL file and add a UTC timestamp."""
    p = Path(path) if path is not None else default_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    record = dict(result)
    record.setdefault("timestamp", utc_now())
    with p.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    return p


def load_records(path=None):
    """Return parsed JSONL values. Malformed lines and blank lines are skipped."""
    p = Path(path) if path is not None else default_path()
    if not p.exists():
        return []
    records = []
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def load_results(path=None):
    return [record for record in load_records(path) if isinstance(record, dict)]


def clear_results(path=None):
    p = Path(path) if path is not None else default_path()
    if p.exists():
        p.unlink()
    return p
