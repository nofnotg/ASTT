from __future__ import annotations

from analysis.big_win_dependency_analyzer import analyze_big_win_dependency
from analysis.tail_risk_analyzer import max_losing_streak


def build_risk_evidence(journal: list[dict]) -> dict:
    dependency = analyze_big_win_dependency("V62_PORTFOLIO", journal)
    flags = [
        {"risk": "Big Win Dependency", "level": "MEDIUM", "evidence": f"Top3 contribution {dependency['top_3_win_contribution_pct']:.2f}%", "action": "Monitor"},
        {"risk": "OHLCV-only Execution", "level": "HIGH", "evidence": "No real spread/depth execution overlay", "action": "Forward overlay required"},
        {"risk": "Trade Concentration", "level": "MEDIUM", "evidence": "Available trades are concentrated in limited dates", "action": "Extend forward paper"},
    ]
    return {
        **dependency,
        "max_losing_streak": max_losing_streak(journal),
        "recovery_time_after_drawdown": "not_enough_calendar_depth",
        "risk_rows": flags,
        "major_risk_flags": [row["risk"] for row in flags if row["level"] in {"HIGH", "MEDIUM"}],
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
