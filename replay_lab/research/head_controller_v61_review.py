from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_head_controller_v61_review(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    root = Path(reports_dir)
    final = _read(root / "latest_v61_final_decision_summary.json")
    robust = _read(root / "latest_v61_strategy_robustness_summary.json")
    best = _best(robust.get("strategies", []))
    worst = _worst(robust.get("strategies", []))
    payload = {
        "schema_version": "v6.1",
        "llm_provider": llm_provider,
        "llm_used": llm_provider != "off",
        "fallback_used": True,
        "live_readiness_opinion": "PAPER_MORE_REQUIRED" if final.get("forward_candidates") else "STRATEGY_REDESIGN_REQUIRED",
        "best_strategy": best,
        "worst_strategy": worst,
        "forward_candidates": final.get("forward_candidates", []),
        "disabled_strategies": final.get("disabled_strategies", []),
        "primary_problem": "LONG_HORIZON_COVERAGE_LIMITED",
        "next_experiments": ["Run V6.2 forward paper on kept strategies", "Collect wider OHLCV coverage", "Add real spread/depth replay before live"],
        "risk_flags": ["real orders disabled", "OHLCV-only execution approximation", "fallback review used"],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "real_order_enabled": False,
    }
    _write(root / "latest_head_controller_v61_review_summary.json", payload)
    _write(Path("replay_store/v61/latest_head_controller_v61_review_summary.json"), payload)
    return payload


def _best(rows: list[dict]) -> str | None:
    scored = [row for row in rows if row.get("trade_count", 0) > 0]
    return max(scored, key=lambda row: row.get("expectancy_pct", 0.0)).get("strategy") if scored else None


def _worst(rows: list[dict]) -> str | None:
    scored = [row for row in rows if row.get("trade_count", 0) > 0]
    return min(scored, key=lambda row: row.get("expectancy_pct", 0.0)).get("strategy") if scored else None


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
