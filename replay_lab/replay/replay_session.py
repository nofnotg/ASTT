from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ReplaySessionConfig(BaseModel):
    session_id: str
    date_kst: date
    markets: list[str]
    scan_time: str = "08:50"
    pre_score_time: str = "08:59"
    monitor_time: str = "09:00"
    decision_time: str = "08:59"
    entry_time: str | None = "09:00"
    target_window_end_time: str = "09:30"
    trade_end_time: str = "10:00"
    mode: str = "PAPER_REPLAY"
    config_version: str = "v0.1"
    strategy_label: str = "0850_0900_scalp"

