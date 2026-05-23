from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR


def store_candidate_second_window(window: dict, store_dir: Path = REPLAY_STORE_DIR) -> dict:
    candidate_id = window["candidate_id"]
    day = pd.Timestamp(window["candidate_time"]).date().isoformat()
    market = window["market"]
    root = store_dir / "candidate_seconds" / day / market
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"{candidate_id}.json"
    parquet_path = root / f"{candidate_id}.parquet"
    json_path.write_text(json.dumps(window, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    pd.DataFrame(window.get("seconds", [])).to_parquet(parquet_path, index=False)
    return {"json_path": str(json_path), "parquet_path": str(parquet_path)}
