from __future__ import annotations


def next_timing_experiments(summary: dict) -> list[str]:
    if summary.get("entry_window_count", 0) == 0:
        return ["Collect more high-volatility event clips", "Tune event detector thresholds", "Review too-early and fake-signal labels"]
    return ["Validate confirmed state forward", "Keep PAPER_MORE_REQUIRED until two-week forward evidence exists"]
