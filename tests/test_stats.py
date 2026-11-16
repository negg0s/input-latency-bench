import json

from input_latency_bench import stats


def test_percentile_interpolates():
    assert stats.percentile([1, 2, 3, 4], 50) == 2.5
    assert stats.percentile([1, 2, 3, 4], 95) == 3.85
    assert stats.percentile([7], 95) == 7.0


def test_summarize_known_values():
    result = stats.summarize([1, 2, 3, 4, 5])
    assert result["count"] == 5
    assert result["min"] == 1
    assert result["median"] == 3
    assert result["p95"] == 4.8
    assert result["p99"] == 4.96
    assert result["max"] == 5
    assert result["mean"] == 3
    assert round(result["stddev"], 4) == 1.4142


def test_summarize_empty():
    result = stats.summarize([])
    assert result["count"] == 0
    assert result["median"] is None
    assert result["p99"] is None
    assert result["stddev"] is None


def test_collect_values_from_jsonl(tmp_path):
    path = tmp_path / "samples.jsonl"
    lines = [
        json.dumps({"command": "keypress", "hold_ms": 10.0}),
        json.dumps({"command": "keypress", "hold_ms": 20.0}),
        json.dumps({"command": "keypress", "interval_ms": 99.0}),
        "not json",
        json.dumps(30.0),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")

    assert stats.collect_values(path) == [10.0, 20.0, 30.0]
    assert stats.collect_values(path, field="interval_ms") == [99.0]


def test_collect_values_dot_path(tmp_path):
    path = tmp_path / "nested.jsonl"
    path.write_text(json.dumps({"result": {"ms": 12.5}}) + "\n", encoding="utf-8")
    assert stats.collect_values(path, field="result.ms") == [12.5]


def test_run_stats_text(tmp_path):
    path = tmp_path / "samples.jsonl"
    path.write_text("1\n2\n3\n4\n", encoding="utf-8")
    out = []
    result = stats.run_stats(path, printer=out.append)
    assert result["count"] == 4
    assert any("median: 2.500" in line for line in out)


def test_run_stats_csv(tmp_path):
    path = tmp_path / "samples.jsonl"
    path.write_text("1\n2\n3\n4\n", encoding="utf-8")
    out = []
    result = stats.run_stats(path, csv_output=True, printer=out.append)
    assert result["count"] == 4
    assert len(out) == 2
    assert "count,min,median,p95,p99,max,mean,stddev" in out[0]
    assert "4,1.000,2.500" in out[1]


def test_summarize_filters_nan_and_inf():
    result = stats.summarize([1, float("nan"), 2, float("inf"), 3])
    assert result["count"] == 3
    assert result["min"] == 1.0
    assert result["median"] == 2.0
    assert result["max"] == 3.0


def test_iqr_small_samples():
    assert stats.iqr([]) == 0.0
    assert stats.iqr([42.0]) == 0.0
    assert stats.iqr([10.0, 20.0]) == 5.0
    assert stats.interquartile_range([1, 2, 3, 4, 5]) == 2.0


def test_outliers_small_samples_returns_empty():
    assert stats.find_outliers([]) == []
    assert stats.find_outliers([5.0]) == []
    assert stats.find_outliers([5.0, 1000.0]) == []
    assert stats.detect_outliers([5.0, 1000.0]) == []
    assert stats.find_outliers([1.0, 2.0, 3.0]) == []


def test_outliers_detection_with_sufficient_samples():
    data = [10.0, 11.0, 12.0, 13.0, 14.0, 100.0]
    outliers = stats.find_outliers(data)
    assert outliers == [100.0]


def test_summarize_includes_iqr():
    empty_res = stats.summarize([])
    assert empty_res["iqr"] is None

    single_res = stats.summarize([7.0])
    assert single_res["iqr"] == 0.0

    double_res = stats.summarize([10.0, 20.0])
    assert double_res["iqr"] == 5.0


def test_jitter_edge_cases():
    # N=0
    assert stats.jitter([]) == 0.0
    assert stats.calculate_jitter([]) == 0.0

    # N=1
    assert stats.jitter([15.0]) == 0.0

    # Identical values
    assert stats.jitter([20.0, 20.0, 20.0]) == 0.0

    # Consecutive differences: |10-12|=2, |15-10|=5 -> (2+5)/2 = 3.5
    assert stats.jitter([12.0, 10.0, 15.0]) == 3.5


def test_z_scores_edge_cases():
    # N=0
    assert stats.z_scores([]) == []
    assert stats.zscore([]) == []

    # N=1 (stddev undefined/zero -> 0.0, no division by zero)
    assert stats.z_scores([50.0]) == [0.0]

    # Identical values (stddev == 0.0 -> no division by zero)
    assert stats.z_scores([42.0, 42.0, 42.0]) == [0.0, 0.0, 0.0]

    # Valid distribution
    scores = stats.z_scores([10.0, 20.0, 30.0])
    assert len(scores) == 3
    assert abs(scores[1]) < 1e-9  # middle is mean -> z=0
    assert round(scores[0], 4) == -1.2247
    assert round(scores[2], 4) == 1.2247


def test_summarize_percentiles_and_edge_cases():
    # N=0
    empty_res = stats.summarize([])
    assert empty_res["p99"] is None
    assert empty_res["p99_9"] is None
    assert empty_res["p99.9"] is None
    assert empty_res["stddev"] is None
    assert empty_res["jitter"] is None

    # N=1
    single_res = stats.summarize([100.0])
    assert single_res["p99"] == 100.0
    assert single_res["p99_9"] == 100.0
    assert single_res["p99.9"] == 100.0
    assert single_res["stddev"] == 0.0
    assert single_res["jitter"] == 0.0

    # All identical values
    identical_res = stats.summarize([50.0, 50.0, 50.0, 50.0])
    assert identical_res["min"] == 50.0
    assert identical_res["max"] == 50.0
    assert identical_res["mean"] == 50.0
    assert identical_res["stddev"] == 0.0
    assert identical_res["jitter"] == 0.0
    assert identical_res["p99"] == 50.0
    assert identical_res["p99_9"] == 50.0


