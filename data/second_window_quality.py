from __future__ import annotations

import pandas as pd


def evaluate_second_window_quality(second_window: dict) -> dict:
    seconds = pd.DataFrame(second_window.get("seconds", []))
    if seconds.empty:
        return {"quality_grade": "UNAVAILABLE", "actual_coverage_pct": 0.0, "critical_window_coverage_pct": 0.0, "missing_ratio": 1.0, "warnings": ["no_seconds"]}
    total = len(seconds)
    actual = int((~seconds.get("synthetic", pd.Series([False] * total)).astype(bool)).sum())
    actual_cov = actual / max(total, 1) * 100
    candidate = pd.Timestamp(second_window["candidate_time"])
    seconds["time"] = pd.to_datetime(seconds["time"])
    critical = seconds[(seconds["time"] >= candidate - pd.Timedelta(seconds=10)) & (seconds["time"] <= candidate + pd.Timedelta(seconds=30))]
    if critical.empty:
        critical_cov = 0.0
    else:
        critical_cov = int((~critical["synthetic"].astype(bool)).sum()) / len(critical) * 100
    missing_ratio = 1 - actual / max(total, 1)
    warnings = []
    if critical_cov == 0:
        warnings.append("critical_window_empty")
    if actual == 0:
        grade = "UNAVAILABLE"
    elif critical_cov >= 30 and actual_cov >= 20:
        grade = "GOOD"
    elif critical_cov > 0 and actual_cov >= 5:
        grade = "PARTIAL"
    else:
        grade = "POOR"
    return {"quality_grade": grade, "actual_coverage_pct": actual_cov, "critical_window_coverage_pct": critical_cov, "missing_ratio": missing_ratio, "warnings": warnings}
