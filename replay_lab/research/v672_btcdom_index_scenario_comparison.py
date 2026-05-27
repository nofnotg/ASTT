from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v672_btcdom_index_rejector import build_v672_rejection_report
from analysis.v672_btcdom_index_saved_loss_missed_profit import extract_v672_saved_loss
from analysis.v672_btcdom_index_yearly_comparator import extract_v672_yearly


def _read_summary(reports_dir: str) -> dict[str, Any]:
    path = Path(reports_dir) / "latest_v672_btcdom_index_scenario_summary.json"
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def build_v672_btcdom_index_saved_loss_report(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = extract_v672_saved_loss(_read_summary(reports_dir))
    _write(Path(reports_dir) / "latest_v672_btcdom_index_saved_loss_summary.json", payload)
    return payload


def build_v672_btcdom_index_yearly_report(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = extract_v672_yearly(_read_summary(reports_dir))
    _write(Path(reports_dir) / "latest_v672_btcdom_index_yearly_summary.json", payload)
    return payload


def build_v672_btcdom_index_rejected_scenarios_report(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = build_v672_rejection_report(_read_summary(reports_dir))
    _write(Path(reports_dir) / "latest_v672_btcdom_index_rejected_scenarios_summary.json", payload)
    return payload


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
