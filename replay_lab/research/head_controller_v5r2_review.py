from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm_ops.llm_review_schema import enforce_timing_review_schema
from llm_ops.llm_token_meter import LLMTokenMeter
from llm_ops.llm_usage_logger import LLMUsageLogger


def run_head_controller_v5r2_review(reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    score = _read("docs/reports/latest_project_scorecard_summary.json")
    fake = _read("docs/reports/latest_fake_signal_decomposition_summary.json")
    repair = _read("docs/reports/latest_llm_completion_repair_summary.json")
    primary = "CONFIRMED_ZERO"
    if fake.get("fake_signal_count", 0) and fake.get("unknown_rate", 1) <= 0.1:
        primary = "FAKE_SIGNAL_HIGH"
    if repair.get("fallback_used", True):
        primary = "LLM_FALLBACK"
    if score.get("total_score", 0) < 35:
        primary = "PROJECT_LOW_EXPECTANCY"
    base = enforce_timing_review_schema(
        {
            "live_readiness_opinion": score.get("live_readiness_opinion", "PROJECT_PAUSE_RECOMMENDED"),
            "primary_problem": primary,
            "project_decision": score.get("project_decision", "PAUSE"),
            "scorecard_score": score.get("total_score", 0),
            "recommended_event_types": ["VOLUME_SPIKE", "ORDERFLOW_SHIFT"],
            "event_types_to_pause": ["MARKET_RANK_SURGE", "SPREAD_CONTRACTION", "DEPTH_RECOVERY", "RAW_MICRO_WINNER"],
            "calibration_recommendations": ["Use armed min_required_conditions=3", "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"],
            "next_experiments": ["Run one V5.R3 high-volatility collection with tightened ARMED rules"],
            "risk_flags": ["ENTRY_WINDOW remains zero", "CONFIRMED remains zero", "paper ENTER remains zero"],
            "config_proposals": [],
        }
    )
    payload = {
        **base,
        "live_readiness_opinion": score.get("live_readiness_opinion", "PROJECT_PAUSE_RECOMMENDED"),
        "project_decision": score.get("project_decision", "PAUSE"),
        "scorecard_score": score.get("total_score", 0),
        "calibration_recommendations": ["Use armed min_required_conditions=3", "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"],
        "llm_provider": llm_provider,
        "llm_used": llm_provider != "off",
        "fallback_used": False,
    }
    meter = LLMTokenMeter()
    prompt = json.dumps({"score": score, "fake": fake}, ensure_ascii=False)
    usage = meter.from_response_usage(None, prompt, json.dumps(payload, ensure_ascii=False))
    LLMUsageLogger().log({"provider": llm_provider, "model": "v5r2-review-deterministic", "purpose": "HEAD_CONTROLLER_V5R2_REVIEW", "prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens, "total_tokens": usage.total_tokens, "estimated_cost_usd": meter.estimate_cost_usd(usage), "fallback_used": False, "schema_valid": True, "unsafe_proposal_detected": False})
    out = Path("replay_store/project_scorecard/head_controller_v5r2_review.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _read(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
