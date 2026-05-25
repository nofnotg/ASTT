from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_head_controller_v64_review(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    root = Path(reports_dir)
    investor = _read(root / "latest_v64_investor_summary.json")
    audit = _read(root / "latest_v64_hindsight_audit_summary.json")
    summary = {
        "llm_provider": llm_provider,
        "llm_used": False,
        "fallback_used": True,
        "live_readiness_opinion": "LIVE_NOT_ALLOWED",
        "primary_problem": "FORWARD_PAPER_NOT_VALIDATED",
        "best_strategy": investor.get("forward_candidate_plan"),
        "defense_validated": audit.get("overall_status") == "PASS",
        "next_experiments": ["V6.5 forward paper에서 Balanced Growth를 켜고 실제 spread/depth overlay를 추가 검증"],
        "risk_flags": ["OHLCV_ONLY_EXECUTION", "NO_REAL_ORDER_VALIDATION"],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "real_order_enabled": False,
    }
    _write(root / "latest_head_controller_v64_review_summary.json", summary)
    return summary


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
