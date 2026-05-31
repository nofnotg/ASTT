from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_head_controller_v673_review(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    root = Path(reports_dir)
    matrix = _read(root / "latest_v673_agent_matrix_summary.json")
    router = _read(root / "latest_v673_scenario_router_summary.json")
    scenarios = list(matrix.get("scenarios", []))
    known = {row.get("scenario") for row in scenarios}
    scenarios.extend(row for row in router.get("scenarios", []) if row and row.get("scenario") not in known)
    candidates = [
        row for row in scenarios
        if str(row.get("decision", "")).endswith("CANDIDATE") or row.get("decision") == "DOMINANCE_FILTER_VALIDATED"
    ]
    payload = {
        "schema_version": "head_controller_v673_review_v1",
        "llm_provider": llm_provider,
        "llm_used": False,
        "fallback_used": True,
        "best_agent": candidates[0].get("scenario") if candidates else None,
        "best_router": "SCENARIO_AGENT_ROUTER_V1" if any(row.get("scenario") == "SCENARIO_AGENT_ROUTER_V1" for row in candidates) else None,
        "rejected_scenarios": [],
        "forward_candidates": [row.get("scenario") for row in candidates],
        "risk_flags": ["PAPER_ONLY", "LIVE_NOT_ALLOWED"],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "real_order_enabled": False,
        "final_decision": "PAPER_MORE_REQUIRED" if not candidates else "SCENARIO_AGENT_ROUTER_CANDIDATE",
    }
    path = Path(reports_dir) / "latest_head_controller_v673_review_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
