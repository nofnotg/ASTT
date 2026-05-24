from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from head_controller.head_controller_experiment_queue import build_experiment_queue
from head_controller.head_controller_risk_score import compute_head_controller_risk_score
from replay_lab.research.artifact_integrity_check_v5561 import check_artifact_integrity_v5561


def run_head_controller_evaluation_loop(reports_dir: str | Path = "docs/reports", llm_provider: str = "off") -> dict:
    reports = Path(reports_dir)
    integrity = check_artifact_integrity_v5561(reports)
    full_seed = _read(reports / "latest_full_seed_allocator_summary.json")
    enter_count = int(full_seed.get("enter_count", 0) or 0)
    primary_problem = "ENTER_0" if enter_count == 0 else "FORWARD_PAPER_REQUIRED"
    risk = compute_head_controller_risk_score({**full_seed, "artifact_integrity_status": integrity["artifact_integrity_status"]})
    result = {
        "evaluation_id": datetime.now().strftime("head_eval_v557_%Y%m%d_%H%M%S"),
        "llm_provider": llm_provider if llm_provider in {"openai", "gemini"} else "off",
        "llm_used": llm_provider in {"openai", "gemini"},
        "fallback_used": False,
        "live_readiness": "LIVE_NOT_ALLOWED",
        "research_score": risk["research_score"],
        "primary_problem": primary_problem,
        "recommended_next_experiments": build_experiment_queue(primary_problem),
        "config_proposals": [],
        "risk_flags": ["PNL_NOT_EVALUABLE"] if enter_count == 0 else [],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "artifact_integrity_status": integrity["artifact_integrity_status"],
    }
    return result


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
