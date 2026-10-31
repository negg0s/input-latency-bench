from unittest.mock import MagicMock, patch

from input_latency_bench import timer


def _make_kernel(values, frequency=10_000_000):
    vals = iter(values)
    mock = MagicMock()
    mock.QueryPerformanceCounter.side_effect = lambda arg: setattr(arg._obj, "value", next(vals))
    mock.QueryPerformanceFrequency.side_effect = lambda arg: setattr(arg._obj, "value", frequency)
    return mock


def test_qpc_reads_counter():
    mock = _make_kernel([42])
    with patch("input_latency_bench.timer.kernel32", mock):
        assert timer.qpc() == 42


def test_qpf_reads_frequency():
    mock = _make_kernel([])
    with patch("input_latency_bench.timer.kernel32", mock):
        assert timer.qpf() == 10_000_000


def test_measure_timer_reports_delta_stats():
    mock = _make_kernel([0, 5, 5, 7, 10])
    with patch("input_latency_bench.timer.kernel32", mock):
        result = timer.measure_timer(samples=4)

    assert result["samples"] == 4
    assert result["frequency"] == 10_000_000
    assert result["tick_ns"] == 100.0
    assert result["zero_delta_count"] == 1
    assert result["min_delta_ticks"] == 0
    assert result["max_delta_ticks"] == 5

    resolution = result["resolution_ns"]
    assert resolution["count"] == 3
    assert resolution["min"] == 200.0
    assert resolution["median"] == 300.0
    assert resolution["p95"] == 480.0
    assert resolution["max"] == 500.0

    overhead = result["overhead_ns"]
    assert overhead["count"] == 4
    assert overhead["min"] == 0.0
    assert overhead["median"] == 250.0
    assert overhead["p95"] == 470.0
    assert overhead["mean"] == 250.0


def test_measure_timer_rejects_bad_samples():
    mock = _make_kernel([])
    with patch("input_latency_bench.timer.kernel32", mock):
        try:
            timer.measure_timer(samples=0)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")
