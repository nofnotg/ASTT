from __future__ import annotations

from pathlib import Path
from typing import Any

import json

from btcd.btcd_feature_builder import BTCDFeatureStore


def build_btcd_data_quality_summary(
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    store = BTCDFeatureStore(archive_dir)
    summary = {
        "schema_version": "v66_btcd_data_quality_v1",
        "data_quality": store.data_quality(),
        "global_btcd_note": "Global BTC Dominance is used only when actual CSV/API data exists. Fake dominance is forbidden.",
        "proxy_note": "Upbit BTC Flow Dominance Proxy is BTC/KRW quote volume divided by total KRW quote volume. It is not global BTC dominance.",
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    path = Path(reports_dir) / "latest_v66_btcd_data_quality_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return summary

