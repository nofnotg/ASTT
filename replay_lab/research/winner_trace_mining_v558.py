from __future__ import annotations

from winner_mining.winner_event_detector import detect_winner_events_from_sessions
from winner_mining.winner_trace_extractor import extract_winner_traces


def detect_winner_events_v558(sessions_dir: str = "replay_store/sessions", winner_types: str = "MICRO_WINNER,SCALP_WINNER,MOMENTUM_WINNER,SPIKE_WINNER") -> dict:
    return detect_winner_events_from_sessions(sessions_dir, winner_types)


def extract_winner_traces_v558(winner_events: str = "replay_store/winner_mining/events", trace_windows: str = "10,30,60,180,300") -> dict:
    return extract_winner_traces(winner_events, trace_windows)
