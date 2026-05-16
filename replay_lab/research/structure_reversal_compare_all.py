from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR, ROOT_DIR
from replay_lab.replay.structure_reversal_v5 import latest_structure_reversal_v5_experiment


def compare_all_strategies_v5(start_date: date, end_date: date, capital_krw: float = 500000, order_krw: float = 10000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "structure_reversal_v5"
    out_dir.mkdir(parents=True, exist_ok=True)
    v3 = _read_json(ROOT_DIR / "docs" / "reports" / "latest_small_seed_summary.json").get("small_seed_result", {})
    v41 = _read_json(ROOT_DIR / "docs" / "reports" / "latest_fear_exhaustion_v41_summary.json").get("small_seed_result", {})
    exp = latest_structure_reversal_v5_experiment(store_dir, mode="small_seed_daily")
    v5 = _read_json(exp / "metrics.json") if exp else {}
    weekly = _latest_weekly_metrics(store_dir)
    verdict = _verdict(v3, v41, v5)
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}, "capital_krw": capital_krw, "order_krw": order_krw, "v3": v3, "v41": v41, "v5": v5, "weekly_sniper": weekly, "verdict": verdict}
    (out_dir / "structure_reversal_compare_all.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def _verdict(v3: dict, v41: dict, v5: dict) -> str:
    if v5.get("entry_count", 0) < 30:
        return "V5_INSUFFICIENT_SAMPLE"
    prior_pf = max(float(v3.get("profit_factor", 0.0) or 0.0), float(v41.get("profit_factor", 0.0) or 0.0))
    if v5.get("account_return_pct", 0.0) <= 0 or v5.get("profit_factor", 0.0) < 0.9:
        return "V5_REJECTED"
    if v5.get("profit_factor", 0.0) > prior_pf and v5.get("consecutive_loss_max", 99) <= min(v3.get("consecutive_loss_max", 99), v41.get("consecutive_loss_max", 99)):
        return "V5_OUTPERFORMS_PRIOR"
    if v5.get("profit_factor", 0.0) > prior_pf:
        return "V5_COMPLEMENTS_PRIOR"
    return "V5_WEAKER_THAN_PRIOR"


def _latest_weekly_metrics(store_dir: Path) -> dict:
    experiments = sorted((store_dir / "experiments").glob("exp_*_structure_reversal_v5"), key=lambda path: path.name)
    for exp in reversed(experiments):
        metrics = _read_json(exp / "metrics.json")
        if metrics.get("mode") == "weekly_sniper":
            return metrics
    return {}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else {}
