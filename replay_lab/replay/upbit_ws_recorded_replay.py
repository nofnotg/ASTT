from __future__ import annotations

from replay_lab.replay.forward_micro_replay import replay_recorded_micro_session


def replay_upbit_ws_recorded_session(session_id: str) -> dict:
    return replay_recorded_micro_session(session_id)
