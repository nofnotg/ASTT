from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ReplaySessionConfig(BaseModel):
    session_id: str
    date_kst: date
    markets: list[str]
    scan_time: str = "08:50"
    pre_score_time: str = "08:55"
    monitor_time: str = "09:00"
    decision_time: str = "09:03"
    trade_end_time: str = "09:30"
    mode: str = "PAPER_REPLAY"
    config_version: str = "v0.1"

