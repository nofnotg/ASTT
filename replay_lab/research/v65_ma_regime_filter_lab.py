from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v65_ma_scenario_analyzer import build_ma_feature_summary, load_true_walk_forward_journal


def build_v65_ma_features(
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    root = Path(reports_dir)
    journal = load_true_walk_forward_journal(root)
    summary = build_ma_feature_summary(journal, archive_dir)
    _write(root / "latest_v65_ma_features_summary.json", summary)
    store = Path("replay_store/v65_ma")
    store.mkdir(parents=True, exist_ok=True)
    _write(store / "latest_v65_ma_features_summary.json", summary)
    return summary


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
