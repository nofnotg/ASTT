from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from data.candidate_second_window_fetcher import fetch_candidate_second_window
from features.micro_candidate_filter import apply_micro_candidate_filter
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.candidate_window_second_replay import replay_candidate_second_window
from replay_lab.research.candidate_second_window_validation import _load_candidates, _metrics


def validate_micro_candidate_filter_v553(start_date, end_date, top_markets: int = 30, max_candidates: int = 50, pre_seconds: int = 120, post_seconds: int = 180, fixed_order_krw: float = 10000) -> dict:
    candidates = _load_candidates(pd.Timestamp(start_date).date(), pd.Timestamp(end_date).date()).head(max_candidates)
    filter_rows = []
    replay_rows = []
    pass_rows = []
    for candidate in candidates.to_dict("records"):
        window = fetch_candidate_second_window(candidate["market"], candidate["candidate_time"], pre_seconds=pre_seconds, post_seconds=post_seconds)
        filter_result = apply_micro_candidate_filter(candidate, window)
        filter_rows.append(filter_result)
        if filter_result["micro_candidate_decision"] != "PASS":
            continue
        replay = replay_candidate_second_window(candidate, window, fixed_order_krw=fixed_order_krw)
        replay["micro_candidate_filter"] = filter_result
        replay_rows.append(replay)
        if replay.get("included_in_pnl") is True:
            pass_rows.append(replay)
    metrics = _metrics(replay_rows)
    result = {
        "before_candidate_count": int(len(candidates)),
        "after_PASS": sum(1 for row in filter_rows if row["micro_candidate_decision"] == "PASS"),
        "after_WATCH": sum(1 for row in filter_rows if row["micro_candidate_decision"] == "WATCH"),
        "after_REJECT": sum(1 for row in filter_rows if row["micro_candidate_decision"] == "REJECT"),
        "pass_enter_count": len(pass_rows),
        "pass_only_pf_realistic_1": metrics["profit_factor_realistic_1"],
        "pass_only_expectancy": metrics["expectancy_realistic_1"],
        "pass_only_total_pnl_krw": metrics["total_pnl_krw_realistic_1"],
        "filter_rows": filter_rows,
        "results": replay_rows,
    }
    out = REPLAY_STORE_DIR / "reports" / "upbit_real_api"
    out.mkdir(parents=True, exist_ok=True)
    (out / "micro_candidate_filter_validation_v553.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result
