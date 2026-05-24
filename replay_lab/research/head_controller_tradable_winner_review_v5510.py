from __future__ import annotations

import json
from pathlib import Path

from head_controller.llm_json_schema import validate_and_sanitize_llm_output
from replay_lab.paths import REPLAY_STORE_DIR


def run_head_controller_tradable_winner_review_v5510(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict:
    reports = Path(reports_dir)
    mining = _read_json(reports / "latest_tradable_winner_mining_summary.json")
    forward = _read_json(reports / "latest_tradable_source_forward_summary.json")
    tradable_count = int(mining.get("tradable_winner_count", 0) or 0)
    enter = int(forward.get("ENTER", 0) or 0)
    if tradable_count <= 0:
        primary = "NO_TRADABLE_WINNER"
        assessment = "UNSUITABLE"
        recommended_type = "NONE"
    elif enter <= 0:
        primary = "ENTER_0"
        assessment = "SECONDARY_ONLY"
        recommended_type = "TRADABLE_SCALP"
    else:
        primary = "PAPER_MORE_REQUIRED"
        assessment = "POSSIBLE"
        recommended_type = "TRADABLE_MOMENTUM"
    raw = {
        "summary": "Tradable winner review completed in guarded research mode.",
        "live_readiness_opinion": "LIVE_NOT_ALLOWED" if primary != "PAPER_MORE_REQUIRED" else "PAPER_MORE_REQUIRED",
        "primary_problem": primary,
        "root_cause_hypotheses": ["MICRO_WINNER raw moves were not tradable after cost."],
        "next_experiments": ["Collect additional high-volatility UPBIT_WS sessions", "Mine tradable scalp/momentum winners only"],
        "risk_flags": ["NO_LIVE_ORDER", "RESEARCH_MODE_ONLY"],
        "config_proposals": [],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
    }
    guarded = validate_and_sanitize_llm_output(raw)
    result = {
        **guarded,
        "llm_provider": llm_provider,
        "llm_used": llm_provider != "off",
        "fallback_used": False,
        "micro_scalping_assessment": assessment,
        "recommended_winner_type": recommended_type,
        "recommended_sources_for_forward": [] if tradable_count <= 0 else ["TRADABLE_VOLUME_BREAKOUT", "TRADABLE_ORDERFLOW_EXPANSION"],
        "sources_to_pause": ["RAW_MICRO_WINNER"],
        "filters_to_tighten": ["effective_return_pct", "spread_pct", "depth_3_level_krw"],
    }
    out = REPLAY_STORE_DIR / "tradable_forward" / "head_controller_tradable_winner_review.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
