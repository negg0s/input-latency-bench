# input-latency-bench

A small Windows CLI for examining QueryPerformanceCounter behavior and
software-observed console key timing. Use it to compare labeled runs on the
same PC, such as timer-read measurements while idle and while a workload is
running. It uses `QueryPerformanceCounter` through `ctypes`, `msvcrt` for
keyboard reads, and stores one JSON record per line.

## What it measures

- `timer`: QueryPerformanceCounter frequency, counter tick length, observed
  counter resolution, and the time cost of back-to-back counter reads.
- `keypress`: time from key-down to key-up (hold time) and the interval between
  successive key-down events.
- `compare`: summarize a numeric field across labeled runs in a JSONL file.
- Summary values: min, median, p95, max, and mean over the collected samples.

All numbers come from software running in the Python process. They describe
what the process can observe, not what a monitor shows.

## What it does not measure

- End-to-end display latency, scan-out, panel response, or frame presentation.
- USB, Bluetooth, or wireless polling delays before Windows delivers an event.
- Kernel input stack time, driver time, or game engine frame latency.
- Any hardware latency that needs a photodiode, high-speed camera, or dedicated
  latency tester to observe.

Treat results as relative measurements between runs on the same machine. Do not
use them as absolute hardware specifications.

## Install

Python 3.9 or newer on Windows.

```powershell
pip install -e . --no-cache-dir
```

For development:

```powershell
pip install -e ".[dev]" --no-cache-dir
```

## Commands

```text
input-latency-bench timer [--samples N] [--label NAME] [--output FILE] [--json]
input-latency-bench keypress [--samples N] [--label NAME] [--output FILE]
input-latency-bench stats FILE [--field FIELD] [--json]
input-latency-bench report [--path FILE] [--json]
input-latency-bench compare FILE [--field FIELD]
input-latency-bench doctor
```

Results are appended to
`%USERPROFILE%\.input-latency-bench\results.jsonl` unless `--output` or
`INPUT_LATENCY_BENCH_HOME` changes the location. Each record gets a UTC
`timestamp` when it is written.

### Repeatable comparison session

This example checks whether the time cost of back-to-back timer reads changes
when a workload is running. Open PowerShell in the same environment, use a new
output file, and keep the machine and power settings unchanged between runs:

```powershell
Remove-Item .\timer-ab.jsonl -ErrorAction SilentlyContinue
input-latency-bench timer --samples 5000 --label idle --output .\timer-ab.jsonl
# Start the workload you want to check, then run:
input-latency-bench timer --samples 5000 --label workload --output .\timer-ab.jsonl
input-latency-bench compare .\timer-ab.jsonl --field overhead_ns.median
```

For a less noisy comparison, repeat each condition several times, appending
each run to the same file. Compare the run medians, not just a single run. The
comparison reports the median, p95, and mean across recorded runs for each
label, plus the median difference from the first label encountered. A label
names a run condition; it does not control or verify that condition.

`examples/timer-comparison.jsonl` is a small synthetic input file. Try it with:

```powershell
input-latency-bench compare examples/timer-comparison.jsonl --field overhead_ns.median
```

This is a software-side diagnostic of timer reads. It cannot establish that a
keyboard, USB connection, display, or game has lower input latency. Keypress
hold values are also affected by when Python reads the key and by polling for
release, so they are not key-switch response-time measurements.

### timer

```powershell
input-latency-bench timer --samples 2000
```

Example output:

```text
frequency: 10000000 Hz
tick: 100.000 ns
samples: 2000
zero deltas: 4
resolution (ns): min=100.000 median=100.000 p95=200.000 max=1900.000 mean=112.400
overhead (ns): min=0.000 median=100.000 p95=300.000 max=1900.000 mean=196.200
```

`resolution` is computed from positive deltas between consecutive reads.
`overhead` includes zero deltas, since a zero delta is a real result of two
reads that landed inside one counter tick.
Pass `--label idle` to save the run with a label for `compare`.

### keypress

```powershell
input-latency-bench keypress --samples 10
```

Press and release a key for each trial. Example output:

```text
Trial 1/10: press and release a key...
  hold 84.213 ms
...
summary:
  count: 10
  hold_ms min: 51.004
  hold_ms median: 78.912
  hold_ms p95: 121.443
  hold_ms max: 143.881
  hold_ms mean: 82.117
  interval_ms min: 210.553
  interval_ms median: 341.295
  interval_ms p95: 702.115
  interval_ms max: 781.002
  interval_ms mean: 390.221
  saved to: C:\Users\you\.input-latency-bench\results.jsonl
```

Key-down is read with `msvcrt.getch()`. Key-up is found by polling
`GetAsyncKeyState` until no key is held. Polling adds roughly one sleep interval
to each hold measurement. Each JSONL trial's `timestamp` is captured just after
the key-down read, in UTC. The hold interval uses QPC ticks, not wall-clock
timestamps.
Pass `--label baseline` to attach the same label to every trial in the run.

### stats

```powershell
input-latency-bench stats results.jsonl --field hold_ms
input-latency-bench stats results.jsonl --field hold_ms --json
```

The file can contain one number per line or one JSON value per line. Without
`--field`, the command looks for `value`, `hold_ms`, `latency_ms`, `ms`, then
`duration_ms`. Dot paths work for nested fields.

### report

```powershell
input-latency-bench report
input-latency-bench report --json
input-latency-bench report --path results.jsonl
```

Text mode prints one block per record. JSON mode prints the parsed records as a
JSON array.

### compare

```powershell
input-latency-bench compare results.jsonl --field hold_ms
input-latency-bench compare results.jsonl --field overhead_ns.median
```

The field can be a nested dot path. Only finite numeric values in records with
a non-empty `label` are included. At least two labels must have values. Older
unlabeled records remain readable by `report` and `stats`, but are not grouped
by `compare`.

### doctor

```powershell
input-latency-bench doctor
```

Checks Python, the platform, QueryPerformanceCounter, `msvcrt`, and the default
storage path.

## Data format

Each line is one JSON object. A timer run produces one line:

```json
{"command":"timer","timestamp":"2026-10-31T12:00:00.000Z","frequency":10000000,"samples":2000,"tick_ns":100.0,"zero_delta_count":4,"resolution_ns":{"count":1996,"min":100.0,"median":100.0,"p95":200.0,"max":1900.0,"mean":112.4},"overhead_ns":{"count":2000,"min":0.0,"median":100.0,"p95":300.0,"max":1900.0,"mean":196.2},"min_delta_ticks":0,"max_delta_ticks":19}
```

A keypress run produces one line per trial:

```json
{"command":"keypress","session":"2026-10-31T12:01:00.000Z","frequency":10000000,"trial":1,"hold_ms":84.213,"interval_ms":null,"timestamp":"2026-10-31T12:01:04.120Z"}
```

## Development

```powershell
pytest
python tools/check_text.py
```

Tests replace the Windows APIs with mocks, so the suite runs without a real
keyboard or console.

## License

MIT. See `LICENSE`.
