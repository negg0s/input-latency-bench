from unittest.mock import MagicMock, patch

from input_latency_bench import keypress


def _kernel(frequency=1_000_000):
    mock = MagicMock()
    mock.QueryPerformanceFrequency.side_effect = lambda arg: setattr(arg._obj, "value", frequency)
    return mock


def test_measure_keypress_hold_and_interval():
    clock_values = iter([0, 100_000, 200_000, 350_000])
    down_values = iter([True, False, True, False])
    reads = []

    def getch():
        reads.append(True)
        return b"a"

    mock_msvcrt = MagicMock()
    mock_msvcrt.getch.side_effect = getch

    with patch(
        "input_latency_bench.storage.utc_now",
        side_effect=["2026-10-31T12:00:00.000Z", "2026-10-31T12:00:01.000Z"],
    ):
        result = keypress.measure_keypress(
            samples=2,
            k32=_kernel(),
            msvcrt_mod=mock_msvcrt,
            printer=lambda *args, **kwargs: None,
            clock=lambda: next(clock_values),
            sleep=lambda seconds: None,
            key_down=lambda: next(down_values),
        )

    assert result["count"] == 2
    assert result["frequency"] == 1_000_000
    assert result["hold_ms"]["count"] == 2
    assert result["hold_ms"]["min"] == 100.0
    assert result["hold_ms"]["max"] == 150.0
    assert result["interval_ms"]["count"] == 1
    assert result["interval_ms"]["min"] == 200.0
    assert result["events"][0]["interval_ms"] is None
    assert result["events"][1]["hold_ms"] == 150.0
    assert result["events"][0]["timestamp"] == "2026-10-31T12:00:00.000Z"
    assert mock_msvcrt.getch.call_count == 2


def test_measure_keypress_requires_msvcrt():
    with patch("input_latency_bench.keypress.msvcrt", None):
        try:
            keypress.measure_keypress(
                samples=1,
                msvcrt_mod=None,
                printer=lambda *args, **kwargs: None,
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected RuntimeError")


def test_measure_keypress_rejects_bad_samples():
    try:
        keypress.measure_keypress(samples=0, msvcrt_mod=MagicMock())
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
