from __future__ import annotations

import json
from pathlib import Path


def run_v62_risk_strengthen_review(reports_dir: str = "docs/reports") -> dict:
    root = Path(reports_dir)
    full = _read(root / "latest_v62_full_investment_summary.json")
    payload = {
        "schema_version": "v6.2",
        "risk": full.get("risk", {}),
        "setup_context_improvement": full.get("setup_context_improvement", []),
        "strengthen_targets": ["FVG_LIQUIDITY_SWEEP", "FVG_OB_OVERLAP", "COMBINED_VOLUME_ICT"],
        "disable_targets": ["DADDY_VOLUME_NECKLINE", "SR_FLIP_RETEST_VOLUME", "FIB_PULLBACK_VOLUME", "PULLBACK_WICK_VOLUME"],
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
    _write(root / "latest_v62_risk_summary.json", payload)
    _write(Path("replay_store/v62/latest_v62_risk_summary.json"), payload)
    return payload


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
