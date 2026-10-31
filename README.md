# input-latency-bench

A small Python CLI for benchmarking **timer resolution/overhead** and **interactive keypress latency** on Windows.

It uses `QueryPerformanceCounter` (QPC) via `ctypes` and `msvcrt` for keypress capture. Results are stored locally and can be reported as text or JSON.

## Safety / accuracy notes

- This tool measures **software-side** timer resolution and keypress-to-timestamp latency.
- It does **not** measure true end-to-end display latency. Real display latency requires external hardware
  (photodiode + oscilloscope, high-speed camera, or a latency tester) because it includes scan-out,
  panel response, and USB/Bluetooth polling delays that software cannot observe.
- Keypress timing is bounded by OS scheduling, USB HID polling (often 1-8 ms), and Python overhead.
- Treat numbers as relative/comparative, not absolute guarantees.

## Install

```bash
pip install -e .
```

## Commands

```bash
input-latency-bench timer        # measure QPC resolution/overhead
input-latency-bench keypress    # interactive keypress latency (press keys, Ctrl+C to stop)
input-latency-bench report      # show stored results
input-latency-bench report --json
input-latency-bench doctor      # environment diagnostics
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
