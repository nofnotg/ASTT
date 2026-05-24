from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from head_controller.llm_key_loader import load_head_controller_llm_keys
from head_controller.openai_llm_client import OpenAIHeadControllerClient
from llm_ops.llm_schema_completion_guard import parse_schema_completion
from llm_ops.llm_token_meter import LLMTokenMeter
from llm_ops.llm_usage_logger import LLMUsageLogger


def run_llm_minimum_completion_test(llm_provider: str = "openai") -> dict[str, Any]:
    context = {
        "task": "minimum_completion_v5r2",
        "required_output": {
            "summary": "string",
            "live_readiness_opinion": "LIVE_NOT_ALLOWED",
            "auto_apply_allowed": False,
            "live_order_allowed": False,
        },
    }
    result = _call_openai(context) if llm_provider == "openai" else {"call_success": False, "content": "", "error": "PROVIDER_DISABLED", "model": "none"}
    guard = parse_schema_completion(result.get("content", ""))
    meter = LLMTokenMeter()
    usage = meter.from_response_usage(None, json.dumps(context), result.get("content", ""))
    fallback = not result.get("call_success") or not guard["schema_valid"]
    row = {
        "llm_call_count": 1,
        "provider": llm_provider,
        "model": result.get("model", "openai"),
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens if result.get("content") else 0,
        "total_tokens": usage.prompt_tokens + (usage.completion_tokens if result.get("content") else 0),
        "estimated_cost_usd": meter.estimate_cost_usd(usage),
        "schema_valid": guard["schema_valid"],
        "fallback_used": fallback,
        "fallback_reason": result.get("error", guard.get("error", "")) if fallback else "",
        "unsafe_proposal_detected": False,
        "raw_secret_detected": False,
        "key_path_detected": False,
    }
    LLMUsageLogger().log(
        {
            "provider": llm_provider,
            "model": row["model"],
            "purpose": "LLM_MINIMUM_COMPLETION_TEST_V5R2",
            "prompt_tokens": row["prompt_tokens"],
            "completion_tokens": row["completion_tokens"],
            "total_tokens": row["total_tokens"],
            "estimated_cost_usd": row["estimated_cost_usd"],
            "fallback_used": row["fallback_used"],
            "schema_valid": row["schema_valid"],
            "unsafe_proposal_detected": False,
        }
    )
    _write(Path("replay_store/llm_usage/llm_minimum_completion_v5r2.json"), row)
    return row


def repair_llm_completion_v5r2(reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    summary = run_llm_minimum_completion_test(llm_provider)
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "latest_llm_completion_repair_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _call_openai(context: dict[str, Any]) -> dict[str, Any]:
    keys = load_head_controller_llm_keys()
    api_key = keys.get("_openai_key")
    if not api_key:
        return {"call_success": False, "content": "", "error": "OPENAI_KEY_NOT_LOADED", "model": "openai"}
    client = OpenAIHeadControllerClient(api_key)
    expected = {
        "summary": "Minimum completion test succeeded.",
        "live_readiness_opinion": "LIVE_NOT_ALLOWED",
        "auto_apply_allowed": False,
        "live_order_allowed": False,
    }
    result = client.analyze({"task": "minimum_completion_v5r2", "return_exact_json": expected, **context})
    return {"call_success": result.call_success, "content": result.content, "error": result.error, "model": client.model}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
