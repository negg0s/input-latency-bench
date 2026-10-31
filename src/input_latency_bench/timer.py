"""QueryPerformanceCounter frequency, resolution, and overhead measurement."""

import ctypes

from .stats import summarize

kernel32 = None


def _load_kernel32():
    global kernel32
    if kernel32 is None:
        kernel32 = ctypes.windll.kernel32
    return kernel32


def qpc(k32=None):
    """Read QueryPerformanceCounter value in ticks."""
    if k32 is None:
        k32 = _load_kernel32()
    counter = ctypes.c_int64()
    k32.QueryPerformanceCounter(ctypes.byref(counter))
    return int(counter.value)


def qpf(k32=None):
    """Read QueryPerformanceFrequency value in ticks per second."""
    if k32 is None:
        k32 = _load_kernel32()
    freq = ctypes.c_int64()
    k32.QueryPerformanceFrequency(ctypes.byref(freq))
    return int(freq.value)


def measure_timer(samples=1000, k32=None):
    """Take ``samples`` consecutive QPC reads and describe the deltas.

    Resolution stats use positive deltas only. Overhead stats include zero
    deltas because a zero delta is a real outcome of back-to-back reads.
    """
    if samples < 1:
        raise ValueError("samples must be >= 1")
    k = k32 if k32 is not None else _load_kernel32()
    freq = qpf(k)
    if freq <= 0:
        raise RuntimeError("QueryPerformanceFrequency returned non-positive value")

    deltas = []
    prev = qpc(k)
    for _ in range(samples):
        cur = qpc(k)
        deltas.append(cur - prev)
        prev = cur

    ns_per_tick = 1e9 / freq
    positive_ns = [d * ns_per_tick for d in deltas if d > 0]
    all_ns = [d * ns_per_tick for d in deltas]

    return {
        "frequency": freq,
        "samples": samples,
        "tick_ns": ns_per_tick,
        "zero_delta_count": sum(1 for d in deltas if d == 0),
        "resolution_ns": summarize(positive_ns),
        "overhead_ns": summarize(all_ns),
        "min_delta_ticks": min(deltas),
        "max_delta_ticks": max(deltas),
    }
