from __future__ import annotations

from pathlib import Path
from typing import Any

from llm_council.llm_config import llm_config
from llm_council.llm_input_pack_builder import build_input_pack
from scenario_telemetry.v688_common import safe_status, write_json


def build_llm_review(review_type: str, reports_dir: str | Path = "docs/reports", provider: str = "openai") -> dict[str, Any]:
    pack = build_input_pack(review_type, reports_dir)
    cfg = llm_config(provider)
    fallback_used = True
    payload = {
        "schema_version": "v688_llm_review_v1",
        "review_id": f"{pack['input_pack_id']}_fallback",
        "review_type": review_type,
        "period": pack.get("period"),
        "model": f"{provider}:fallback_rule_based",
        "input_pack_id": pack.get("input_pack_id"),
        "summary": "Rule-based review generated from engine summaries. Raw logs were not sent to any LLM.",
        "key_findings": _findings(pack),
        "risk_flags": ["LIVE_NOT_ALLOWED", "MANUAL_REVIEW_REQUIRED"],
        "scenario_feedback": [],
        "recommended_experiments": [row.get("recommendation_id") for row in pack.get("active_analysis_recommendations", [])],
        "promotion_candidates": [],
        "demotion_candidates": [],
        "manual_review_required": True,
        "active_change_applied": False,
        "live_order_allowed": False,
        "llm_used": False,
        "fallback_used": fallback_used,
        "api_key_present": cfg["api_key_present"],
        "api_key_value_stored": False,
        "token_budget": pack.get("token_budget"),
        **safe_status(),
    }
    name = {"daily": "daily_review", "weekly": "weekly_council", "monthly": "monthly_deck_review"}.get(review_type, f"{review_type}_review")
    write_json(Path(reports_dir) / f"latest_v688_llm_{name}_summary.json", payload)
    return payload


def _findings(pack: dict[str, Any]) -> list[str]:
    findings = []
    if pack.get("candidates_count", 0) and not pack.get("entries_count", 0):
        findings.append("후보는 있었지만 진입은 없었습니다. skip reason audit이 필요합니다.")
    if pack.get("pipeline_health", {}).get("ledger_update_stale"):
        findings.append("forward 후보 로그와 paper ledger 갱신 상태가 분리되어 있습니다.")
    if not findings:
        findings.append("특이 trigger가 크지 않아 paper observation을 유지합니다.")
    return findings
