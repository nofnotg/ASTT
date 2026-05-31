from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v673_high_watermark_analyzer import build_v673_high_watermark_report as _hwm
from analysis.v673_rejected_scenario_cleaner import build_v673_rejection_report
from analysis.v673_saved_loss_missed_profit import extract_v673_saved_loss
from analysis.v673_yearly_market_state_comparator import extract_v673_yearly


def build_v673_high_watermark_report(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = _hwm(_read_matrix(reports_dir))
    _write(Path(reports_dir) / "latest_v673_high_watermark_summary.json", payload)
    return payload


def build_v673_rejected_scenarios_report(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = build_v673_rejection_report(_read_matrix(reports_dir))
    _write(Path(reports_dir) / "latest_v673_rejected_scenarios_summary.json", payload)
    return payload


def build_v673_saved_loss_report(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = extract_v673_saved_loss(_read_matrix(reports_dir))
    _write(Path(reports_dir) / "latest_v673_saved_loss_missed_profit_summary.json", payload)
    return payload


def build_v673_yearly_market_state_report(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = extract_v673_yearly(_read_matrix(reports_dir))
    _write(Path(reports_dir) / "latest_v673_yearly_market_state_summary.json", payload)
    return payload


def _read_matrix(reports_dir: str) -> dict[str, Any]:
    root = Path(reports_dir)
    matrix_path = root / "latest_v673_agent_matrix_summary.json"
    router_path = root / "latest_v673_scenario_router_summary.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8-sig")) if matrix_path.exists() else {}
    router = json.loads(router_path.read_text(encoding="utf-8-sig")) if router_path.exists() else {}
    if not matrix:
        return router
    known = {row.get("scenario") for row in matrix.get("scenarios", [])}
    merged = dict(matrix)
    merged["scenarios"] = list(matrix.get("scenarios", [])) + [
        row for row in router.get("scenarios", []) if row and row.get("scenario") not in known
    ]
    if router.get("lookahead_audit"):
        merged["lookahead_audit"] = router["lookahead_audit"]
    if router.get("market_state_pnl"):
        merged["market_state_pnl"] = router["market_state_pnl"]
    return merged


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
