from __future__ import annotations

import json
from pathlib import Path

from head_controller.llm_json_schema import validate_and_sanitize_llm_output
from replay_lab.paths import REPLAY_STORE_DIR


def run_head_controller_false_positive_review_v559(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict:
    fp = _load(REPLAY_STORE_DIR / "false_positive" / "false_positive_control.json")
    refined = _load(REPLAY_STORE_DIR / "false_positive" / "refined_source_validation.json")
    forward = _load(REPLAY_STORE_DIR / "forward_v559" / "latest_forward_summary.json")
    recommended = [r["source"] for r in refined.get("refined_source_results", []) if r.get("precision", 0.0) >= 0.20 and r.get("fpr", 1.0) <= 0.60]
    primary = "ENTER_0" if not forward.get("ENTER", 0) else "FORWARD_READY_NOT_PROVEN"
    if not recommended:
        primary = "FALSE_POSITIVE_HIGH"
    output = {
        "summary": "False positive review completed in guarded research mode.",
        "live_readiness_opinion": "LIVE_NOT_ALLOWED",
        "primary_problem": primary,
        "root_cause_hypotheses": ["Refined source precision must be proven out of sample."],
        "next_experiments": ["Collect high-volatility forward sessions for refined sources"],
        "risk_flags": ["RESEARCH_MODE_ONLY", "NO_LIVE_ORDER"],
        "config_proposals": [],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
    }
    sanitized = validate_and_sanitize_llm_output(output)
    result = {
        **sanitized,
        "llm_provider": llm_provider,
        "llm_used": llm_provider != "off",
        "fallback_used": False,
        "recommended_sources_for_forward": recommended,
        "sources_to_pause": [r["source"] for r in fp.get("source_results", []) if r.get("precision", 0.0) < 0.20],
        "filters_to_tighten": ["spread_pct", "tradable_depth", "tick_noise", "volume_burst"],
    }
    out = REPLAY_STORE_DIR / "false_positive" / "head_controller_false_positive_review.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
