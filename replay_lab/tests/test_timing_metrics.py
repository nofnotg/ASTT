from timing_lab.timing_metrics import build_timing_metrics


def test_timing_metrics_counts_entry_window_rate_and_abort_reasons():
    metrics = build_timing_metrics([{}], [{}], [{"label": "ENTRY_WINDOW"}], {"abort_reason_counts": {"SPREAD_TOO_WIDE": 1}})
    assert metrics["entry_window_rate"] == 1.0
    assert metrics["abort_reason_counts"]["SPREAD_TOO_WIDE"] == 1
