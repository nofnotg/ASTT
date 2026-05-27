from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from btcd.btcd_data_quality import build_v67_global_btcd_quality
from btcd.coinmarketcap_global_client import save_cmc_btc_dominance_history
from btcd.global_btcd_collector import collect_current_global_btcd


def prepare_v67_global_btcd_data(
    reports_dir: str = "docs/reports",
    history_path: str = "data/external/btc_dominance_history.csv",
    use_available_history: bool = True,
) -> dict[str, Any]:
    current = collect_current_global_btcd("coinpaprika", save=True)
    cmc_result = {"saved": False, "quality": {"reason": "SKIPPED_EXISTING_HISTORY"}}
    if use_available_history and not Path(history_path).exists():
        cmc_result = save_cmc_btc_dominance_history(
            output_path=history_path,
            start="2022-01-01T00:00:00Z",
            end=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            interval="1d",
        )
    quality = build_v67_global_btcd_quality(history_path)
    summary = {
        "schema_version": "v67_global_btcd_data_preparation_v1",
        "coinpaprika_current": _safe_current(current),
        "coinmarketcap_historical": _safe_quality(cmc_result),
        "data_quality": quality,
        "fake_data_generated": False,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(Path(reports_dir) / "latest_v67_global_btcd_data_quality_summary.json", quality)
    _write(Path(reports_dir) / "latest_v67_global_btcd_data_preparation_summary.json", summary)
    return summary


def build_v67_global_btcd_data_quality_report(
    reports_dir: str = "docs/reports",
    history_path: str = "data/external/btc_dominance_history.csv",
) -> dict[str, Any]:
    quality = build_v67_global_btcd_quality(history_path)
    _write(Path(reports_dir) / "latest_v67_global_btcd_data_quality_summary.json", quality)
    return quality


def _safe_current(current: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": current.get("source", "coinpaprika"),
        "available": current.get("dominance") is not None,
        "dominance": current.get("dominance"),
        "fetched_at": current.get("fetched_at"),
        "validation": current.get("validation", {}),
    }


def _safe_quality(result: dict[str, Any]) -> dict[str, Any]:
    quality = result.get("quality", {})
    return {
        "saved": result.get("saved", False),
        "rows": result.get("rows", 0),
        "source": quality.get("source", "coinmarketcap"),
        "available": quality.get("available", False),
        "period": quality.get("period", "unavailable"),
        "coverage": quality.get("coverage", "0%"),
        "reason": quality.get("reason"),
        "notes": quality.get("notes"),
    }


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
