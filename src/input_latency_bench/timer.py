"""QueryPerformanceCounter based timer resolution/overhead measurement."""

import ctypes

kernel32 = None


def _load_kernel32():
    global kernel32
    if kernel32 is None:
        kernel32 = ctypes.windll.kernel32
    return kernel32


def qpc(k32=None):
    """Read QueryPerformanceCounter value."""
    if k32 is None:
        k32 = _load_kernel32()
    counter = ctypes.c_int64()
    k32.QueryPerformanceCounter(ctypes.byref(counter))
    return int(counter.value)


def qpf(k32=None):
    """Read QueryPerformanceFrequency value."""
    if k32 is None:
        k32 = _load_kernel32()
    freq = ctypes.c_int64()
    k32.QueryPerformanceFrequency(ctypes.byref(freq))
    return int(freq.value)


def measure_timer(samples=1000, k32=None):
    """Measure timer resolution and per-call overhead.

    Returns a dict with frequency, samples, resolution_ns (min positive delta),
    overhead_ns (mean delta between consecutive calls), and zero_delta_count.
    """
    if samples < 1:
        raise ValueError("samples must be >= 1")
    k = k32 if k32 is not None else _load_kernel32()
    freq = qpf(k)
    if freq <= 0:
        raise RuntimeError("QueryPerformanceFrequency returned non-positive value")

    deltas = []
    zeros = 0
    prev = qpc(k)
    for _ in range(samples):
        cur = qpc(k)
        d = cur - prev
        if d == 0:
            zeros += 1
        else:
            deltas.append(d)
        prev = cur

    if deltas:
        resolution_ticks = min(deltas)
        mean_ticks = sum(deltas + [0] * zeros) / samples if samples else 0
        # mean over all samples including zeros for overhead
        all_deltas = []
        # recompute mean including zeros as 0 ticks
        total_ticks = sum(deltas)  # zeros contribute 0
        mean_ticks = total_ticks / samples
    else:
        resolution_ticks = 0
        mean_ticks = 0

    ns_per_tick = 1e9 / freq
    return {
        "frequency": freq,
        "samples": samples,
        "resolution_ns": resolution_ticks * ns_per_tick,
        "overhead_ns": mean_ticks * ns_per_tick,
        "zero_delta_count": zeros,
        "min_delta_ticks": (min(deltas) if deltas else 0),
    }
