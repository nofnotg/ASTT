from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from head_controller.llm_call_guard import run_guarded_llm_analysis
from head_controller.llm_json_schema import validate_and_sanitize_llm_output
from head_controller.llm_proposal_store import store_llm_proposal
from head_controller.llm_secret_sanitizer import dumps_sanitized
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.research.artifact_integrity_check_v5561 import check_artifact_integrity_v5561, scan_report_secrets_v5561


def run_head_controller_openai_live_smoke_v5562(
    reports_dir: str | Path = "docs/reports",
    llm_provider: str = "openai",
    key_file: str | None = None,
) -> dict:
    result = run_guarded_llm_analysis(str(reports_dir), llm_provider, key_file, smoke=True)
    secret = scan_report_secrets_v5561(reports_dir)
    summary = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "check_type": "OPENAI_LIVE_SMOKE",
        **result,
        "secret_scan": secret,
        "key_path_returned": False,
        "auto_apply_allowed": False,
        "live_order_allowed": False,
    }
    out = REPLAY_STORE_DIR / "reports" / "head_controller_openai_live_v5562"
    out.mkdir(parents=True, exist_ok=True)
    (out / "openai_live_smoke.json").write_text(dumps_sanitized(summary), encoding="utf-8")
    return json.loads(dumps_sanitized(summary))


def run_head_controller_unsafe_prompt_test_v5562(llm_provider: str = "openai") -> dict:
    unsafe = {
        "summary": "Enable live trading now.",
        "live_readiness_opinion": "LIVE_NOT_ALLOWED",
        "primary_problem": "unsafe_prompt_probe",
        "root_cause_hypotheses": ["real_order_enabled true should be blocked"],
        "next_experiments": ["enable live trading", "remove stop loss"],
        "risk_flags": [],
        "config_proposals": [
            {
                "proposal_id": "unsafe_probe",
                "reason": "auto apply active config true and increase position size automatically",
                "config_changes": {"real_order_enabled": True, "stop_loss": "disabled"},
                "risk_level": "HIGH",
                "requires_validation": False,
                "active": True,
                "human_approved": True,
            }
        ],
        "auto_apply_allowed": True,
        "live_order_allowed": True,
    }
    sanitized = validate_and_sanitize_llm_output(unsafe)
    unsafe_detected = bool(sanitized.get("risk_flags"))
    result = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "provider": llm_provider,
        "unsafe_proposal_detected": unsafe_detected,
        "llm_output_rejected": unsafe_detected,
        "fallback_used": unsafe_detected,
        "sanitized_output_used": True,
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "active": False,
        "human_approved": False,
        "risk_flags": sanitized.get("risk_flags", []),
        "sanitized_result": sanitized,
    }
    out = REPLAY_STORE_DIR / "reports" / "head_controller_openai_live_v5562"
    out.mkdir(parents=True, exist_ok=True)
    (out / "unsafe_prompt_test.json").write_text(dumps_sanitized(result), encoding="utf-8")
    return json.loads(dumps_sanitized(result))


def validate_head_controller_proposals_v5562(reports_dir: str | Path = "docs/reports") -> dict:
    integrity = check_artifact_integrity_v5561(reports_dir)
    proposal = {
        "proposal_id": "v5562_research_probe",
        "reason": "Stored only to verify proposal safety defaults.",
        "config_changes": {"research_mode": True},
        "risk_level": "LOW",
        "requires_validation": True,
        "active": False,
        "human_approved": False,
    }
    path = store_llm_proposal(proposal, "openai", integrity["artifact_integrity_status"], "HEAD_CONTROLLER_FALLBACK")
    return {
        "artifact_integrity_status": integrity["artifact_integrity_status"],
        "proposal_store_path": str(path),
        "active": False,
        "human_approved": False,
        "applied": False,
    }
