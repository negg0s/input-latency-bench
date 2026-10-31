"""Interactive keypress latency measurement using msvcrt."""

import statistics

try:
    import msvcrt
except ImportError:  # pragma: no cover - non-Windows
    msvcrt = None

from . import timer


def _stats(values):
    if not values:
        return {"count": 0, "min_ms": 0.0, "max_ms": 0.0, "mean_ms": 0.0, "median_ms": 0.0}
    return {
        "count": len(values),
        "min_ms": min(values),
        "max_ms": max(values),
        "mean_ms": statistics.fmean(values),
        "median_ms": statistics.median(values),
    }


def measure_keypress(samples=5, k32=None, msvcrt_mod=None, printer=print):
    """Run interactive keypress latency trials.

    Returns a dict containing latencies_ms and summary stats.
    """
    if samples < 1:
        raise ValueError("samples must be >= 1")
    if msvcrt_mod is None:
        msvcrt_mod = msvcrt
    if msvcrt_mod is None:
        raise RuntimeError("msvcrt is not available (Windows only)")

    freq = timer.qpf(k32)
    if freq <= 0:
        raise RuntimeError("QueryPerformanceFrequency returned non-positive value")

    latencies = []
    try:
        for i in range(samples):
            printer(f"Trial {i + 1}/{samples}: press any key...")
            t0 = timer.qpc(k32)
            msvcrt_mod.getch()
            t1 = timer.qpc(k32)
            ms = (t1 - t0) * 1000.0 / freq
            latencies.append(ms)
            printer(f"  {ms:.2f} ms")
    except KeyboardInterrupt:
        printer("\nInterrupted by user.")

    result = _stats(latencies)
    result["latencies_ms"] = latencies
    result["frequency"] = freq
    return result
