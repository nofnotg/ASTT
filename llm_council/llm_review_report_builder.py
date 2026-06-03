from __future__ import annotations

from pathlib import Path

from scenario_telemetry.v688_common import read_json, write_html


def build_llm_review_report(reports_dir: str | Path = "docs/reports") -> str:
    reports = Path(reports_dir)
    daily = read_json(reports / "latest_v688_llm_daily_review_summary.json")
    weekly = read_json(reports / "latest_v688_llm_weekly_council_summary.json")
    monthly = read_json(reports / "latest_v688_llm_monthly_deck_review_summary.json")
    return write_html(
        reports / "latest_v688_llm_review_report.html",
        "V6.8.8 LLM Review Loop",
        [("Daily Review", daily), ("Weekly Council", weekly), ("Monthly Deck Review", monthly)],
    )
