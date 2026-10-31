import ctypes
from unittest.mock import MagicMock, patch

from input_latency_bench import timer


def _make_kernel(values):
    vals = iter(values)
    mock = MagicMock()
    mock.QueryPerformanceCounter.side_effect = lambda arg: setattr(arg._obj, "value", next(vals))
    mock.QueryPerformanceFrequency.side_effect = lambda arg: setattr(arg._obj, "value", 10_000_000)
    return mock


def test_qpc_reads_counter():
    mock = _make_kernel([42])
    # frequency call not needed
    mock.QueryPerformanceFrequency.side_effect = lambda arg: setattr(arg._obj, "value", 10_000_000)
    with patch("input_latency_bench.timer.kernel32", mock):
        assert timer.qpc() == 42


def test_qpf_reads_frequency():
    mock = _make_kernel([])
    with patch("input_latency_bench.timer.kernel32", mock):
        assert timer.qpf() == 10_000_000


def test_measure_timer_resolution_and_overhead():
    # 5 calls: counter values increasing
    mock = _make_kernel([0, 5, 5, 7, 10, 12])
    # need 1 initial + 5 samples = 6 qpc calls -> values count 6
    with patch("input_latency_bench.timer.kernel32", mock):
        res = timer.measure_timer(samples=5)
    assert res["samples"] == 5
    assert res["frequency"] == 10_000_000
    # deltas: 5,0,2,3,2 -> min positive 2 ticks -> ns
    assert res["min_delta_ticks"] == 2
    assert res["zero_delta_count"] == 1
    assert res["resolution_ns"] == 2 * 100.0  # 1e9/1e7 = 100 ns per tick


def test_measure_timer_validation():
    mock = _make_kernel([])
    with patch("input_latency_bench.timer.kernel32", mock):
        try:
            timer.measure_timer(samples=0)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")
