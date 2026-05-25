from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_head_controller_v65_review(
    reports_dir: str = "docs/reports",
    llm_provider: str = "openai",
) -> dict[str, Any]:
    root = Path(reports_dir)
    scenario = _read(root / "latest_v65_ma_scenario_summary.json")
    recommendation = scenario.get("recommendation", {})
    best = recommendation.get("best_scenario", "NONE")
    judgement = recommendation.get("final_judgement", "MA_FILTER_REJECTED")
    review = {
        "schema_version": "head_controller_v65_review_v1",
        "llm_provider": llm_provider,
        "llm_used": False,
        "fallback_used": True,
        "best_scenario": best,
        "rejected_scenario": "MA_SQUEEZE_RESEARCH" if best != "MA_SQUEEZE_RESEARCH" else "NONE",
        "recommended_policy": best,
        "next_forward_candidate": best if judgement in {"POLICY_ROUTER_CANDIDATE", "MA_FILTER_VALIDATED"} else "NONE",
        "risk_flags": [
            "LIVE_NOT_ALLOWED",
            "MA is used only as filter/router, not standalone buy trigger",
            "OHLCV-only validation still needs spread/depth forward overlay",
        ],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "real_order_enabled": False,
    }
    _write(root / "latest_head_controller_v65_review_summary.json", review)
    return review


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
