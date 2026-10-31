"""Reporting of stored benchmark results."""

import json

from . import storage


def run_report(json_output=False, path=None, printer=print):
    data = storage.load_results(path)
    if json_output:
        printer(json.dumps(data, indent=2))
        return data
    if not data:
        printer("No stored results. Run 'timer' or 'keypress' first.")
        return data
    for idx, entry in enumerate(data, 1):
        printer(f"--- Result {idx} ---")
        printer(f"command: {entry.get('command', 'unknown')}")
        for k, v in entry.items():
            if k == "command":
                continue
            printer(f"  {k}: {v}")
    return data
