import pytest

from input_latency_bench import report


def test_compare_groups_labeled_nested_values(tmp_path):
    path = tmp_path / "runs.jsonl"
    path.write_text(
        '\n'.join(
            [
                '{"command":"timer","label":"idle","overhead_ns":{"median":100}}',
                '{"command":"timer","label":"idle","overhead_ns":{"median":120}}',
                '{"command":"timer","label":"load","overhead_ns":{"median":200}}',
                '{"command":"timer","overhead_ns":{"median":999}}',
            ]
        ),
        encoding="utf-8",
    )
    output = []

    result = report.run_compare(path, field="overhead_ns.median", printer=output.append)

    assert list(result) == ["idle", "load"]
    assert result["idle"]["count"] == 2
    assert result["idle"]["median"] == 110
    assert result["load"]["median"] == 200
    assert "load vs idle" in "\n".join(output)
    assert "90.000" in "\n".join(output)


def test_compare_requires_two_labeled_groups(tmp_path):
    path = tmp_path / "runs.jsonl"
    path.write_text('{"label":"only","hold_ms":12}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="at least two labeled runs"):
        report.run_compare(path, field="hold_ms", printer=lambda _: None)
