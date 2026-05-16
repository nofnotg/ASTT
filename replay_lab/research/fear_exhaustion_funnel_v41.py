from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fear_exhaustion_v41 import FearExhaustionV41Config, default_min_drop_pct, scan_fear_exhaustion_v41


FUNNEL_KEYS = [
    "total_bars",
    "drop_event_count",
    "low_retest_or_lower_low_count",
    "fear_cooling_count",
    "bollinger_reentry_count",
    "min_support_context_count",
    "v41_score_pass_count",
    "skeptic_pass_count",
    "skeptic_warn_count",
    "skeptic_reject_count",
    "final_entry_count",
]


def build_fear_exhaustion_funnel_v41(
    start_date: date,
    end_date: date,
    markets: list[str],
    timeframes: list[str],
    top_markets: int = 50,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    out_dir = store_dir / "reports" / "fear_exhaustion_v41"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    funnels = {}
    for timeframe in timeframes:
        config = FearExhaustionV41Config(timeframe=timeframe, min_drop_pct=default_min_drop_pct(timeframe))
        _, _, funnel = scan_fear_exhaustion_v41(start_date, end_date, markets[:top_markets], 500000, 10000, config, store_dir)
        funnels[timeframe] = funnel
        rows.append({**funnel, "bottleneck_stage": bottleneck_stage(funnel)})
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "funnels": funnels,
        "rows": rows,
    }
    (out_dir / "fear_exhaustion_funnel_v41.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_parquet(out_dir / "fear_exhaustion_funnel_v41.parquet", index=False)
    return out_dir


def bottleneck_stage(funnel: dict) -> str:
    ordered = [
        "total_bars",
        "drop_event_count",
        "low_retest_or_lower_low_count",
        "fear_cooling_count",
        "bollinger_reentry_count",
        "min_support_context_count",
        "v41_score_pass_count",
        "final_entry_count",
    ]
    worst_stage = ordered[1]
    worst_ratio = 1.0
    prev = max(1, int(funnel.get(ordered[0], 0)))
    for key in ordered[1:]:
        current = int(funnel.get(key, 0))
        ratio = current / prev if prev else 0.0
        if ratio < worst_ratio:
            worst_ratio = ratio
            worst_stage = key
        prev = max(1, current)
    return worst_stage
