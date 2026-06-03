from __future__ import annotations

from pathlib import Path
from typing import Any

from scenario_telemetry.v688_common import ACTIVE_ROUTE, SHADOW_ROUTES, load_context, safe_status, write_html, write_json


def build_scenario_disagreement_matrix(
    initial_cash_krw: float = 500000.0,
    use_available_history: bool = True,
    reports_dir: str | Path = "docs/reports",
    data_dir: str | Path = "data/paper",
) -> dict[str, Any]:
    ctx = load_context(reports_dir, data_dir)
    rows = []
    for event in ctx["forward_events"]:
        active = event.get("entry_decision", "WAIT")
        shadow_decisions = {route: "WAIT" for route in SHADOW_ROUTES}
        dtype = "ALL_SKIP_BUT_OUTCOME_UNKNOWN" if active != "ENTER" else "ACTIVE_ENTER_SHADOW_WAIT_OUTCOME_UNKNOWN"
        rows.append(
            {
                "event_id": event.get("event_id"),
                "timestamp": event.get("timestamp"),
                "market": event.get("market"),
                "candidate_score": event.get("candidate_score"),
                "market_state": "FORWARD_MICRO",
                "expected_rr": event.get("expected_rr"),
                "support_proximity": event.get("support_proximity"),
                "resistance_distance": event.get("resistance_distance"),
                "active_decision": active,
                "shadow_decisions": shadow_decisions,
                "realized_outcome_after_1h": None,
                "realized_outcome_after_4h": None,
                "realized_outcome_after_1d": None,
                "best_decision_ex_post": "UNKNOWN_NO_EX_POST_DATA",
                "active_missed_profit": 0.0,
                "active_saved_loss": 0.0,
                "disagreement_type": dtype,
                "lesson": "Forward 후보는 있으나 ex-post outcome 데이터가 부족해 승패 판단은 보류합니다.",
            }
        )
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["disagreement_type"]] = counts.get(row["disagreement_type"], 0) + 1
    payload = {
        "schema_version": "v688_scenario_disagreement_v1",
        "initial_cash_krw": initial_cash_krw,
        "use_available_history": bool(use_available_history),
        "active_route": ACTIVE_ROUTE,
        "rows": rows,
        "type_counts": counts,
        "row_count": len(rows),
        **safe_status(),
    }
    reports = Path(reports_dir)
    write_json(reports / "latest_v688_scenario_disagreement_summary.json", payload)
    write_html(
        reports / "latest_v688_scenario_disagreement_report.html",
        "V6.8.8 Scenario Disagreement Matrix",
        [("Disagreement Rows", rows), ("Type Counts", counts)],
    )
    return payload
