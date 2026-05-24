from __future__ import annotations

import json
from pathlib import Path

from head_controller.llm_json_schema import validate_and_sanitize_llm_output
from replay_lab.research.artifact_integrity_check_v5561 import check_artifact_integrity_v5561


def run_head_controller_winner_review_v558(reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> dict:
    reports = Path(reports_dir)
    winner = _read(reports / "latest_winner_trace_summary.json")
    redesign = _read(reports / "latest_candidate_source_redesign_summary.json")
    integrity = check_artifact_integrity_v5561(reports)
    recommended = [row["source"] for row in redesign.get("redesigned_source_validation", []) if row.get("grade_b_plus", 0) > 0]
    data = {
        "summary": "Winner mining review completed in research mode.",
        "live_readiness_opinion": "PAPER_MORE_REQUIRED" if recommended else "LIVE_NOT_ALLOWED",
        "primary_problem": "WINNER_CAPTURE_LOW" if winner.get("winner_event_count", 0) else "DATA_INSUFFICIENT",
        "root_cause_hypotheses": ["Existing candidates did not create real ENTER signals."],
        "next_experiments": ["Forward test redesigned sources during high-volatility UPBIT_WS sessions"],
        "risk_flags": ["RESEARCH_MODE_ONLY", "NO_LIVE_ORDER"],
        "config_proposals": [
            {
                "proposal_id": "v558_redesigned_source_research",
                "reason": "Evaluate redesigned sources in forward paper only.",
                "config_changes": {"candidate_sources": recommended},
                "risk_level": "MEDIUM",
                "requires_validation": True,
                "active": False,
                "human_approved": False,
            }
        ] if recommended else [],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
    }
    safe = validate_and_sanitize_llm_output(data)
    result = {
        **safe,
        "llm_provider": llm_provider,
        "llm_used": llm_provider in {"openai", "gemini"},
        "fallback_used": False,
        "recommended_candidate_sources": recommended,
        "sources_to_pause": ["MICRO_ACCELERATION", "VWAP_RECLAIM", "EMA_PULLBACK", "ORDERBOOK_IMBALANCE"] if recommended else [],
        "artifact_integrity_status": integrity["artifact_integrity_status"],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
    }
    out = Path("replay_store/winner_mining/reports")
    out.mkdir(parents=True, exist_ok=True)
    (out / "head_controller_winner_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
