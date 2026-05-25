from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.defense_vs_growth_tradeoff import summarize_defense_growth_tradeoff


def build_v64_investor_summary(reports_dir: str = "docs/reports") -> dict[str, Any]:
    root = Path(reports_dir)
    causal = _read(root / "latest_v64_causal_defense_summary.json")
    amp = _read(root / "latest_v64_return_amplification_summary.json")
    audit = _read(root / "latest_v64_hindsight_audit_summary.json")
    comparison = _read(root / "latest_v64_scenario_comparison_summary.json")
    scenarios = causal.get("scenarios", [])
    best_forward = _best_forward(scenarios)
    summary = {
        "schema_version": "v64_investor_summary_v1",
        "one_line_conclusion": "정답지 사용 감사가 PASS라면 Balanced Growth를 V6.5 forward paper 후보로 두고, Aggressive Growth는 별도 연구 후보로 검증합니다.",
        "defense_validated": audit.get("overall_status") == "PASS" and _mdd_improved(scenarios),
        "hindsight_risk": "LOW" if audit.get("overall_status") == "PASS" else "HIGH",
        "recommended_defense_policy": "BALANCED_GROWTH",
        "recommended_growth_policy": amp.get("best_growth_scenario"),
        "forward_candidate_plan": best_forward.get("scenario"),
        "final_judgement": "DEFENSE_VALIDATED" if audit.get("overall_status") == "PASS" else "DEFENSE_REJECTED",
        "tradeoff": summarize_defense_growth_tradeoff(causal),
        "scenario_comparison": comparison.get("scenarios", []),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(root / "latest_v64_investor_summary.json", summary)
    return summary


def _best_forward(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in scenarios if row.get("scenario") in {"BALANCED_GROWTH", "AGGRESSIVE_GROWTH", "ROLLING_EDGE_THROTTLE"}]
    return max(candidates, key=lambda row: float(row.get("capital", {}).get("return_to_mdd_ratio", 0.0))) if candidates else {}


def _mdd_improved(scenarios: list[dict[str, Any]]) -> bool:
    baseline = next((row for row in scenarios if row.get("scenario") == "BASELINE"), {})
    balanced = next((row for row in scenarios if row.get("scenario") == "BALANCED_GROWTH"), {})
    return float(balanced.get("capital", {}).get("max_drawdown_pct", 0.0)) > float(baseline.get("capital", {}).get("max_drawdown_pct", 0.0))


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
