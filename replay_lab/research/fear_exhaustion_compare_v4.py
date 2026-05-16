from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from replay_lab.paths import REPLAY_STORE_DIR


def compare_v4_v41(
    start_date: date,
    end_date: date,
    capital_krw: float = 500000,
    order_krw: float = 10000,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    out_dir = store_dir / "reports" / "fear_exhaustion_v41"
    out_dir.mkdir(parents=True, exist_ok=True)
    v4_summary = _read_json(Path("docs/reports/latest_fear_divergence_summary.json"))
    v41_sweep = _read_json(out_dir / "fear_exhaustion_sweep_v41.json")
    v41_report = _read_json(out_dir / "fear_exhaustion_v41_report.json")
    v4_result = v4_summary.get("v4_result", {})
    best = v41_sweep.get("best", {})
    v41_result = v41_report.get("metrics") or best
    verdict = _verdict(v4_result, best)
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "v4": {
            "entry_count": v4_result.get("entry_count", 0),
            "live_readiness": v4_summary.get("live_readiness", "LIVE_NOT_ALLOWED"),
            "profit_factor": v4_result.get("profit_factor", 0.0),
            "account_return_pct": v4_result.get("account_return_pct", 0.0),
        },
        "v41": {
            "entry_count": v41_result.get("entry_count", 0),
            "live_readiness": v41_report.get("live_readiness", "LIVE_NOT_ALLOWED"),
            "profit_factor": v41_result.get("profit_factor", 0.0),
            "account_return_pct": v41_result.get("account_return_pct", 0.0),
            "best_timeframe": best.get("timeframe", ""),
            "best_config": best,
            "funnel_bottleneck": _bottleneck(v41_sweep),
        },
        "verdict": verdict,
    }
    (out_dir / "fear_exhaustion_compare_v4.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def _verdict(v4: dict, best: dict) -> str:
    v41_entries = int(best.get("entry_count", 0) or 0)
    if v41_entries < 30:
        return "V41_STILL_NO_SAMPLE"
    if best.get("status") == "STRATEGY_VALID":
        return "V41_STRATEGY_VALID"
    if best.get("account_return_pct", 0.0) <= 0 or best.get("profit_factor", 0.0) < 1.0:
        return "V41_REJECTED"
    if v41_entries > int(v4.get("entry_count", 0) or 0):
        return "V41_CREATES_SAMPLE"
    return "V41_WEAK_BUT_PROMISING"


def _bottleneck(sweep: dict) -> dict:
    best_tf = sweep.get("best", {}).get("timeframe")
    funnel = sweep.get("base_funnels", {}).get(best_tf, {}) if best_tf else {}
    keys = [
        "total_bars",
        "drop_event_count",
        "low_retest_or_lower_low_count",
        "fear_cooling_count",
        "bollinger_reentry_count",
        "min_support_context_count",
        "v41_score_pass_count",
        "final_entry_count",
    ]
    previous = None
    worst = {"stage": "", "survival_ratio": 1.0}
    for key in keys:
        value = float(funnel.get(key, 0) or 0)
        if previous and previous > 0:
            ratio = value / previous
            if ratio < worst["survival_ratio"]:
                worst = {"stage": key, "survival_ratio": ratio}
        previous = value
    return worst


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
