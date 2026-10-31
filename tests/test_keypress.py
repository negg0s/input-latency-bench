from unittest.mock import MagicMock, patch

from input_latency_bench import keypress, timer


def _make_kernel(values):
    vals = iter(values)
    mock = MagicMock()
    mock.QueryPerformanceCounter.side_effect = lambda arg: setattr(arg._obj, "value", next(vals))
    mock.QueryPerformanceFrequency.side_effect = lambda arg: setattr(arg._obj, "value", 10_000_000)
    return mock


def test_measure_keypress_collects_latencies():
    mock_k = _make_kernel([0, 100, 200, 300])
    mock_ms = MagicMock()
    mock_ms.getch.return_value = b"a"
    with patch("input_latency_bench.keypress.msvcrt", mock_ms), patch(
        "input_latency_bench.timer.kernel32", mock_k
    ):
        res = keypress.measure_keypress(samples=2, printer=lambda *a, **k: None)
    assert res["count"] == 2
    assert len(res["latencies_ms"]) == 2
    assert res["min_ms"] > 0
    assert mock_ms.getch.call_count == 2


def test_measure_keypress_no_msvcrt():
    with patch("input_latency_bench.keypress.msvcrt", None):
        try:
            keypress.measure_keypress(samples=1, msvcrt_mod=None, printer=lambda *a, **k: None)
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected RuntimeError")
