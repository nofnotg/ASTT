from __future__ import annotations

import json
from pathlib import Path


def run_head_controller_v62_review(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict:
    root = Path(reports_dir)
    full = _read(root / "latest_v62_full_investment_summary.json")
    capital = full.get("capital", {})
    payload = {
        "schema_version": "v6.2",
        "llm_provider": llm_provider,
        "llm_used": llm_provider != "off",
        "fallback_used": True,
        "live_readiness_opinion": "PAPER_MORE_REQUIRED",
        "best_plan": "PLAN_A_ICT_FAT_TAIL",
        "forward_candidates": ["PLAN_A_ICT_FAT_TAIL", "PLAN_B_COMBINED_CONTEXT"],
        "disabled_strategies": ["DADDY_VOLUME_NECKLINE"],
        "primary_problem": "FORWARD_SPREAD_DEPTH_NOT_VALIDATED",
        "capital_result": capital,
        "next_experiments": ["Run V6.3 forward paper with real spread/depth overlay", "Track FVG_LIQUIDITY_SWEEP recurrence", "Keep DaddyBTC as context only"],
        "risk_flags": full.get("risk", {}).get("major_risk_flags", []),
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "real_order_enabled": False,
    }
    _write(root / "latest_head_controller_v62_review_summary.json", payload)
    _write(Path("replay_store/v62/latest_head_controller_v62_review_summary.json"), payload)
    return payload


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
