from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from data.candidate_second_window_fetcher import fetch_candidate_second_window
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.candidate_window_second_replay import replay_candidate_second_window
from replay_lab.replay.edge_isolation_v54 import latest_edge_isolation_v54_experiment


def validate_candidate_second_windows(start_date, end_date, top_markets: int = 30, pre_seconds: int = 120, post_seconds: int = 180, fixed_order_krw: float = 10000, max_candidates: int = 50, output_name: str = "candidate_second_window_validation.json") -> dict:
    candidates = _load_candidates(pd.Timestamp(start_date).date(), pd.Timestamp(end_date).date()).head(max_candidates)
    rows = []
    quality_counts = {"GOOD": 0, "PARTIAL": 0, "POOR": 0, "UNAVAILABLE": 0}
    for candidate in candidates.to_dict("records"):
        window = fetch_candidate_second_window(candidate["market"], candidate["candidate_time"], pre_seconds=pre_seconds, post_seconds=post_seconds)
        quality_counts[window["data_quality"]] = quality_counts.get(window["data_quality"], 0) + 1
        if window["data_quality"] in {"GOOD", "PARTIAL"}:
            rows.append(replay_candidate_second_window(candidate, window, fixed_order_krw=fixed_order_krw))
    result = _metrics(rows)
    result.update({"candidate_count": int(len(candidates)), "second_window_fetched_count": int(sum(quality_counts.values())), "good_window_count": quality_counts.get("GOOD", 0), "partial_window_count": quality_counts.get("PARTIAL", 0), "good_partial_count": quality_counts.get("GOOD", 0) + quality_counts.get("PARTIAL", 0), "poor_window_count": quality_counts.get("POOR", 0), "unavailable_window_count": quality_counts.get("UNAVAILABLE", 0), "pre_seconds": pre_seconds, "post_seconds": post_seconds, "data_source": "UPBIT_REST_SECONDS", "results": rows})
    out = REPLAY_STORE_DIR / "reports" / "upbit_real_api"
    out.mkdir(parents=True, exist_ok=True)
    (out / output_name).write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    if output_name != "candidate_second_window_validation.json":
        (out / "candidate_second_window_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def validate_candidate_second_windows_v553(start_date, end_date, top_markets: int = 30, pre_seconds: int = 120, post_seconds: int = 180, fixed_order_krw: float = 10000, max_candidates: int = 50) -> dict:
    return validate_candidate_second_windows(start_date, end_date, top_markets=top_markets, pre_seconds=pre_seconds, post_seconds=post_seconds, fixed_order_krw=fixed_order_krw, max_candidates=max_candidates, output_name="candidate_second_window_validation_v553.json")


def _load_candidates(start: date, end: date) -> pd.DataFrame:
    exp = latest_edge_isolation_v54_experiment(REPLAY_STORE_DIR)
    if exp and (exp / "edge_trades.parquet").exists():
        frame = pd.read_parquet(exp / "edge_trades.parquet")
        frame = frame[(frame["strategy_id"] == "MTF_ONLY") & (frame["exit_model"] == "FIXED_RR_1_5")].copy()
        frame["candidate_time"] = frame["entry_time_kst"]
        mask = (pd.to_datetime(frame["date_kst"]).dt.date >= start) & (pd.to_datetime(frame["date_kst"]).dt.date <= end)
        return frame[mask][["market", "candidate_time", "entry_price", "target_price", "stop_price"]].rename(columns={"entry_price": "reference_price"})
    return pd.DataFrame(columns=["market", "candidate_time", "reference_price", "target_price", "stop_price"])


def _metrics(rows: list[dict]) -> dict:
    entered = [r for r in rows if r.get("included_in_pnl") is True and r.get("entry_decision") == "ENTER"]
    pnl = [float(r.get("net_pnl_pct", 0.0)) for r in entered if r.get("net_pnl_pct") is not None]
    gross = [float(r.get("gross_pnl_pct", 0.0)) for r in entered if r.get("gross_pnl_pct") is not None]
    wins = [x for x in pnl if x > 0]
    losses = [x for x in pnl if x < 0]
    gwins = [x for x in gross if x > 0]
    glosses = [x for x in gross if x < 0]
    enter_count = sum(1 for r in rows if r.get("entry_decision") == "ENTER")
    wait_count = sum(1 for r in rows if r.get("entry_decision") == "WAIT")
    cancel_count = sum(1 for r in rows if r.get("entry_decision") == "CANCEL")
    return {"entry_count": len(entered), "enter_count": enter_count, "wait_count": wait_count, "cancel_count": cancel_count, "observation_only_count": sum(1 for r in rows if r.get("observation_only") is True), "win_rate": len(wins) / len(entered) if entered else 0.0, "profit_factor_gross": sum(gwins) / abs(sum(glosses)) if glosses else (999.0 if gwins else 0.0), "profit_factor_realistic_1": sum(wins) / abs(sum(losses)) if losses else (999.0 if wins else 0.0), "expectancy_realistic_1": sum(pnl) / len(pnl) if pnl else 0.0, "total_pnl_krw_realistic_1": sum(float(r.get("net_pnl_krw", 0.0)) for r in entered if r.get("net_pnl_krw") is not None), "avg_hold_seconds": sum(float(r.get("hold_seconds", 0.0)) for r in entered) / len(entered) if entered else 0.0, "micro_failure_exit_count": sum(1 for r in entered if r.get("exit_reason") == "MICRO_FAILURE_EXIT"), "time_stop_count": sum(1 for r in entered if r.get("exit_reason") == "TIME_STOP")}
