from __future__ import annotations

from winner_mining.winner_capture_analyzer import analyze_winner_capture_rate


def analyze_winner_capture_rate_v558(winner_traces: str = "replay_store/winner_mining/traces", candidate_sources: str = "MICRO_ACCELERATION,VWAP_RECLAIM,EMA_PULLBACK,ORDERBOOK_IMBALANCE") -> dict:
    return analyze_winner_capture_rate(winner_traces, candidate_sources)
