"""Interactive keypress timing using msvcrt and QueryPerformanceCounter."""

import ctypes
import time

try:
    import msvcrt
except ImportError:  # pragma: no cover - non-Windows
    msvcrt = None

from . import storage, timer
from .stats import summarize


def _any_key_down():
    user32 = ctypes.windll.user32
    for vk in range(0x08, 0xFF):
        if user32.GetAsyncKeyState(vk) & 0x8000:
            return True
    return False


def measure_keypress(
    samples=5,
    k32=None,
    msvcrt_mod=None,
    printer=print,
    clock=None,
    sleep=None,
    key_down=None,
    poll_interval=0.001,
):
    """Measure key hold time and time between successive key-down events.

    ``clock`` returns QPC ticks. ``key_down`` reports whether any key is
    currently held. Both are replaceable so the timing loop can be tested
    without a console.
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

    if clock is None:
        clock = lambda: timer.qpc(k32)
    if sleep is None:
        sleep = time.sleep
    if key_down is None:
        key_down = _any_key_down

    events = []
    previous_down = None
    try:
        for index in range(samples):
            printer(f"Trial {index + 1}/{samples}: press and release a key...")
            msvcrt_mod.getch()
            down_ticks = clock()
            timestamp = storage.utc_now()
            while key_down():
                sleep(poll_interval)
            up_ticks = clock()

            hold_ms = (up_ticks - down_ticks) * 1000.0 / freq
            interval_ms = None
            if previous_down is not None:
                interval_ms = (down_ticks - previous_down) * 1000.0 / freq
            previous_down = down_ticks
            events.append(
                {
                    "trial": index + 1,
                    "timestamp": timestamp,
                    "hold_ms": hold_ms,
                    "interval_ms": interval_ms,
                }
            )
            printer(f"  hold {hold_ms:.3f} ms")
    except KeyboardInterrupt:
        printer("\nInterrupted by user.")

    return {
        "frequency": freq,
        "count": len(events),
        "hold_ms": summarize([event["hold_ms"] for event in events]),
        "interval_ms": summarize(
            [event["interval_ms"] for event in events if event["interval_ms"] is not None]
        ),
        "events": events,
    }
