from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from btcd.btcdom_index_normalizer import normalize_btcdom_index_files
from btcd.uploaded_btcdom_csv_loader import copy_uploaded_btcdom_csvs


def prepare_v673_dominance_data(
    source_dir: str = "C:/ASTT",
    use_available_history: bool = True,
    reports_dir: str = "docs/reports",
) -> dict[str, Any]:
    copied = copy_uploaded_btcdom_csvs(source_dir=source_dir, external_dir="data/external")
    quality = normalize_btcdom_index_files("data/external", "data/processed")
    quality["schema_version"] = "v673_dominance_data_quality_v1"
    quality["copied_files"] = copied
    quality["use_available_history"] = use_available_history
    _write(Path(reports_dir) / "latest_v673_dominance_data_quality_summary.json", quality)
    return quality


def build_v673_dominance_data_quality_report(reports_dir: str = "docs/reports") -> dict[str, Any]:
    path = Path(reports_dir) / "latest_v673_dominance_data_quality_summary.json"
    quality = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else normalize_btcdom_index_files("data/external", "data/processed")
    quality["schema_version"] = "v673_dominance_data_quality_v1"
    _write(path, quality)
    return quality


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
