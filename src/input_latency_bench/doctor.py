"""Environment diagnostics."""

import platform
import sys

from . import timer


def run_doctor(k32=None, printer=print):
    checks = []

    checks.append(("python_version", True, sys.version.split()[0]))
    checks.append(("platform", platform.system() == "Windows", platform.system()))

    # QueryPerformanceCounter
    try:
        freq = timer.qpf(k32)
        checks.append(("query_performance_counter", True, f"frequency={freq} Hz"))
    except Exception as exc:  # noqa: BLE001
        checks.append(("query_performance_counter", False, str(exc)))

    # msvcrt
    try:
        import msvcrt  # noqa: F401
        checks.append(("msvcrt", True, "available"))
    except ImportError:
        checks.append(("msvcrt", False, "not available (Windows only)"))

    # storage
    from . import storage

    p = storage.default_path()
    checks.append(("storage_path", True, str(p)))

    for name, ok, detail in checks:
        printer(f"[{'OK' if ok else 'FAIL'}] {name}: {detail}")
    return checks
