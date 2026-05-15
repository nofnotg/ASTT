from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fear_divergence_v4 import latest_fear_divergence_experiment


def compare_v3_v4(
    start_date: date,
    end_date: date,
    capital_krw: float = 500000,
    order_krw: float = 10000,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    out_dir = store_dir / "reports" / "fear_divergence_v4"
    out_dir.mkdir(parents=True, exist_ok=True)
    v3 = _read_json(store_dir / "reports" / "small_seed_v3" / "small_seed_v3_report.json").get("small_seed_result", {})
    exp = latest_fear_divergence_experiment(store_dir)
    v4 = _read_json(exp / "metrics.json") if exp else {}
    verdict = _verdict(v3, v4)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "v3": v3,
        "v4": v4,
        "verdict": verdict,
    }
    (out_dir / "fear_divergence_compare_v3.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def _verdict(v3: dict, v4: dict) -> str:
    if v4.get("entry_count", 0) < 30:
        return "V4_INSUFFICIENT_SAMPLE"
    if v4.get("account_return_pct", 0) > v3.get("account_return_pct", 0) and v4.get("profit_factor", 0) > v3.get("profit_factor", 0):
        return "V4_OUTPERFORMS_V3"
    if v4.get("account_return_pct", 0) > 0 and v3.get("account_return_pct", 0) <= 0:
        return "V4_COMPLEMENTS_V3"
    return "V4_WEAKER_THAN_V3"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else {}
