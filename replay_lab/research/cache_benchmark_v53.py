from __future__ import annotations

import json
import time
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from features.feature_snapshot_cache import get_or_build_feature_snapshot
from replay_lab.paths import REPLAY_STORE_DIR


def benchmark_cache_v53(start_date: date, end_date: date, top_markets: int = 30, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "fractal_v53"
    out_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame({"time": pd.date_range(start=start_date, periods=120, freq="min"), "close": range(120)})
    benchmark_id = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    config = {"version": "v53", "top_markets": top_markets, "benchmark_id": benchmark_id}
    start = time.perf_counter()
    first = [get_or_build_feature_snapshot(f"KRW-TEST{i}", frame.iloc[-1]["time"], {"1m": frame}, config) for i in range(8)]
    cache_off_time = time.perf_counter() - start
    start = time.perf_counter()
    second = [get_or_build_feature_snapshot(f"KRW-TEST{i}", frame.iloc[-1]["time"], {"1m": frame}, config) for i in range(8)]
    cache_on_time = time.perf_counter() - start
    hit_rate = sum(1 for item in second if item["cache_hit"]) / len(second)
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "cache_hit_rate": hit_rate, "cache_off_time": cache_off_time, "cache_on_time": cache_on_time, "speedup_ratio": cache_off_time / cache_on_time if cache_on_time else 0.0, "full_validation_estimated_time": cache_on_time * max(1, top_markets) * 10}
    (out_dir / "cache_benchmark_v53.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir
