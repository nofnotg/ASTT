from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


def ensure_naive_or_same_tz(left: datetime, right: datetime) -> None:
    if (left.tzinfo is None) != (right.tzinfo is None):
        raise ValueError("ReplayClock comparisons require consistent timezone awareness")


@dataclass
class ReplayClock:
    current_time_kst: datetime

    def set(self, dt: datetime) -> None:
        self.current_time_kst = dt

    def advance_to(self, dt: datetime) -> None:
        ensure_naive_or_same_tz(dt, self.current_time_kst)
        if dt < self.current_time_kst:
            raise ValueError("Cannot move replay clock backwards unless reset is explicit")
        self.current_time_kst = dt

    def assert_not_future(self, data_time: datetime) -> None:
        ensure_naive_or_same_tz(data_time, self.current_time_kst)
        if data_time > self.current_time_kst:
            raise RuntimeError("Lookahead bias detected")

