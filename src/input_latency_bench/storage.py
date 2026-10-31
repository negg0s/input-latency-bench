"""Local result storage (JSON)."""

import json
import os
from pathlib import Path


def default_path():
    base = os.environ.get("INPUT_LATENCY_BENCH_HOME")
    if base:
        return Path(base) / "results.json"
    return Path.home() / ".input-latency-bench" / "results.json"


def load_results(path=None):
    p = Path(path) if path is not None else default_path()
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return data


def save_result(result, path=None):
    p = Path(path) if path is not None else default_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    data = load_results(p)
    data.append(result)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def clear_results(path=None):
    p = Path(path) if path is not None else default_path()
    if p.exists():
        p.unlink()
    return p
