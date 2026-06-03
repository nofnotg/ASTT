from __future__ import annotations

from pathlib import Path
from typing import Any

from scenario_telemetry.v688_common import load_context, safe_status, top_counts, write_html, write_json


def build_missed_opportunity_analysis(
    initial_cash_krw: float = 500000.0,
    use_available_history: bool = True,
    reports_dir: str | Path = "docs/reports",
    data_dir: str | Path = "data/paper",
) -> dict[str, Any]:
    ctx = load_context(reports_dir, data_dir)
    events = ctx["forward_events"]
    blocked = [event for event in events if event.get("entry_decision", "WAIT") != "ENTER"]
    reasons = [event.get("primary_block_reason") for event in blocked]
    payload = {
        "schema_version": "v688_missed_opportunity_v1",
        "candidate_count": len(events),
        "missed_opportunity_count": len(blocked),
        "missed_profit_1h": None,
        "missed_profit_4h": None,
        "missed_profit_1d": None,
        "saved_loss_count": 0,
        "saved_loss_amount": 0.0,
        "false_block_rate": None,
        "valid_block_rate": None,
        "top_false_block_reasons": top_counts(reasons),
        "decision": "PAPER_MORE_REQUIRED" if blocked else "NO_MISSED_OPPORTUNITY",
        "notes": "ex-post outcome 데이터가 없으면 false/valid block rate는 계산하지 않습니다.",
        "rows": blocked,
        **safe_status(),
    }
    reports = Path(reports_dir)
    write_json(reports / "latest_v688_missed_opportunity_summary.json", payload)
    write_html(
        reports / "latest_v688_missed_opportunity_report.html",
        "V6.8.8 Missed Opportunity",
        [("Summary", payload), ("Blocked Candidate Rows", blocked)],
    )
    return payload
