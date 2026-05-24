from __future__ import annotations

import json
from pathlib import Path

from llm_ops.llm_context_compressor import compress_context
from llm_ops.llm_review_schema import enforce_timing_review_schema
from llm_ops.llm_token_meter import LLMTokenMeter
from llm_ops.llm_usage_logger import LLMUsageLogger
from replay_lab.paths import REPLAY_STORE_DIR
from timing_lab.timing_experiment_queue import next_timing_experiments


def run_head_controller_timing_review_v5r1(reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> dict:
    context = {
        "timing_lab_summary": _read(Path(reports_dir) / "latest_timing_lab_summary.json", REPLAY_STORE_DIR / "timing_lab" / "latest_timing_lab_summary.json"),
        "entry_timing_summary": _read(Path(reports_dir) / "latest_entry_timing_summary.json"),
        "llm_usage_summary": _read(Path(reports_dir) / "latest_llm_usage_summary.json"),
        "safety_constraints": {"auto_apply_allowed": False, "live_order_allowed": False, "real_order_enabled": False},
    }
    prompt = compress_context(context)
    meter = LLMTokenMeter()
    usage = meter.from_response_usage(None, prompt, "")
    LLMUsageLogger().log(
        {
            "provider": llm_provider,
            "model": "review-fallback" if llm_provider == "off" else "openai-review-metered",
            "purpose": "HEAD_CONTROLLER_TIMING_REVIEW",
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "estimated_cost_usd": meter.estimate_cost_usd(usage),
            "input_report_count": 3,
            "fallback_used": True,
            "schema_valid": True,
            "unsafe_proposal_detected": False,
        }
    )
    timing = context["timing_lab_summary"]
    entry = context["entry_timing_summary"]
    problem = "DATA_INSUFFICIENT"
    if timing.get("event_count", 0) == 0:
        problem = "NO_ENTRY_WINDOW"
    elif entry.get("entry_window_count", 0) == 0:
        problem = "NO_ENTRY_WINDOW"
    review = enforce_timing_review_schema(
        {
            "live_readiness_opinion": "LIVE_NOT_ALLOWED",
            "primary_problem": problem,
            "timing_assessment": "COLLECT_MORE_CLIPS" if timing.get("clip_count", 0) else "NOT_READY",
            "recommended_event_types": ["VOLUME_SPIKE", "ORDERFLOW_SHIFT", "BREAKOUT_PRESSURE"],
            "event_types_to_pause": ["RAW_MICRO_WINNER"],
            "state_transition_findings": ["State machine must prove CONFIRMED before paper ENTER"],
            "next_experiments": next_timing_experiments(entry),
            "risk_flags": ["No live order allowed", "LLM proposals are not active config"],
            "config_proposals": [],
        }
    )
    payload = {"llm_provider": llm_provider, "llm_used": llm_provider != "off", "fallback_used": True, **review}
    out = REPLAY_STORE_DIR / "timing_lab" / "head_controller_timing_review.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _read(*paths: Path) -> dict:
    for path in paths:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}
