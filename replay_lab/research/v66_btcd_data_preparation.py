from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v66_btcd_inclusion_auditor import write_btcd_inclusion_audit
from btcd.btcd_data_quality_reporter import build_btcd_data_quality_summary
from btcd.btcd_feature_builder import BTCDFeatureStore


def audit_v66_btcd_inclusion(reports_dir: str = "docs/reports") -> dict[str, Any]:
    return write_btcd_inclusion_audit(reports_dir)


def prepare_v66_btcd_data(
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    store = BTCDFeatureStore(archive_dir)
    summary = {
        "schema_version": "v66_btcd_preparation_v1",
        "data_quality": store.data_quality(),
        "global_btcd_available": bool(store.data_quality()["global_btc_dominance"].get("available")),
        "upbit_proxy_available": bool(store.data_quality()["upbit_btc_flow_dominance_proxy"].get("available")),
        "fake_dominance_generated": False,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(Path(reports_dir) / "latest_v66_btcd_data_preparation_summary.json", summary)
    return summary


def build_v66_btcd_data_quality_report(
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    return build_btcd_data_quality_summary(reports_dir, archive_dir)


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

