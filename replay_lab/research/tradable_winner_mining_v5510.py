from __future__ import annotations

from tradable_winner.tradable_winner_detector import detect_tradable_winners_from_recorded_sessions
from tradable_winner.tradable_trace_extractor import extract_tradable_traces


def mine_tradable_winners_v5510(sessions_dir: str, initial_cash_krw: float, winner_types: str | list[str]) -> dict:
    types = [w.strip() for w in winner_types.split(",") if w.strip()] if isinstance(winner_types, str) else winner_types
    return detect_tradable_winners_from_recorded_sessions(sessions_dir, initial_cash_krw, types)


def extract_tradable_traces_v5510(winner_dir: str, trace_windows: str | list[int]) -> dict:
    windows = [int(w.strip()) for w in trace_windows.split(",") if w.strip()] if isinstance(trace_windows, str) else trace_windows
    return extract_tradable_traces(winner_dir, windows)
