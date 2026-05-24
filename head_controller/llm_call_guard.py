from __future__ import annotations

import json

from artifact_integrity.report_artifact_validator import validate_report_artifacts
from head_controller.gemini_llm_client import GeminiHeadControllerClient
from head_controller.llm_config import build_head_controller_llm_config
from head_controller.llm_fallback_analyzer import fallback_head_controller_analysis
from head_controller.llm_json_schema import validate_and_sanitize_llm_output
from head_controller.llm_key_loader import load_head_controller_llm_keys
from head_controller.llm_proposal_store import store_llm_proposal
from head_controller.llm_secret_sanitizer import sanitize_for_report
from head_controller.openai_llm_client import OpenAIHeadControllerClient
from head_controller.head_controller_context_builder import build_head_controller_context


def run_guarded_llm_analysis(reports_dir: str, llm_provider: str = "auto", key_file: str | None = None, smoke: bool = False) -> dict:
    integrity = validate_report_artifacts(reports_dir)
    llm_config = build_head_controller_llm_config(llm_provider, key_file)
    context = build_head_controller_context(reports_dir, llm_config)
    if integrity["artifact_integrity_status"] == "FAIL":
        result = fallback_head_controller_analysis(context, "ARTIFACT_INTEGRITY_FAIL")
        return _finish(result, integrity, llm_config, False, False, True, "artifact_fail")
    if not llm_config["llm_enabled"]:
        result = fallback_head_controller_analysis(context, "LLM_OFF_OR_KEY_MISSING")
        return _finish(result, integrity, llm_config, False, False, True, "llm_unavailable")
    keys = load_head_controller_llm_keys(key_file)
    client = OpenAIHeadControllerClient(keys["_openai_key"]) if llm_config["selected_provider"] == "openai" else GeminiHeadControllerClient(keys["_gemini_key"])
    if smoke:
        llm_result = client.analyze({"task": "smoke", "instruction": "Return a safe research-only status. Do not suggest or mention live trading enablement.", "constraints": context["constraints"]})
    else:
        llm_result = client.analyze(sanitize_for_report(context))
    if not llm_result.call_success:
        result = fallback_head_controller_analysis(context, f"API_FAIL:{llm_result.error}")
        return _finish(result, integrity, llm_config, False, False, True, llm_result.error)
    try:
        parsed = json.loads(_strip_fence(llm_result.content))
        result = validate_and_sanitize_llm_output(parsed)
        result["fallback_used"] = False
        result["llm_output_rejected"] = False
        schema_valid = True
        if "LLM_UNSAFE_PROPOSAL_REJECTED" in result.get("risk_flags", []):
            rejected = result
            result = fallback_head_controller_analysis(context, "UNSAFE_LLM_OUTPUT")
            result["risk_flags"] = list(set(result.get("risk_flags", []) + rejected.get("risk_flags", [])))
            result["llm_output_rejected"] = True
            schema_valid = True
    except Exception as exc:
        result = fallback_head_controller_analysis(context, f"SCHEMA_FAIL:{type(exc).__name__}")
        result["llm_output_rejected"] = True
        schema_valid = False
    proposal_paths = []
    for proposal in result.get("config_proposals", []):
        proposal_paths.append(str(store_llm_proposal(proposal, llm_config["selected_provider"], integrity["artifact_integrity_status"], "HEAD_CONTROLLER_LLM" if schema_valid else "HEAD_CONTROLLER_FALLBACK")))
    return _finish(result, integrity, llm_config, True, schema_valid, result.get("fallback_used", False), "", proposal_paths)


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


def _finish(result: dict, integrity: dict, llm_config: dict, call_success: bool, schema_valid: bool, fallback_used: bool, error: str, proposal_paths=None) -> dict:
    return sanitize_for_report({
        **result,
        "artifact_integrity": integrity,
        "llm_config": llm_config,
        "provider": llm_config.get("selected_provider", "off"),
        "call_success": call_success,
        "schema_valid": schema_valid,
        "fallback_used": fallback_used,
        "unsafe_proposal_detected": "LLM_UNSAFE_PROPOSAL_REJECTED" in result.get("risk_flags", []),
        "proposal_store_paths": proposal_paths or [],
        "error": error,
        "auto_apply_allowed": False,
        "live_order_allowed": False,
    })
