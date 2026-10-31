from unittest.mock import MagicMock, patch

from input_latency_bench import doctor, timer


def _make_kernel():
    mock = MagicMock()
    mock.QueryPerformanceFrequency.side_effect = lambda arg: setattr(arg._obj, "value", 10_000_000)
    return mock


def test_doctor_runs():
    mock = _make_kernel()
    with patch("input_latency_bench.timer.kernel32", mock):
        out = []
        checks = doctor.run_doctor(k32=mock, printer=out.append)
    assert isinstance(checks, list)
    assert any(c[0] == "query_performance_counter" and c[1] for c in checks)
    assert any("OK" in s or "FAIL" in s for s in out)
