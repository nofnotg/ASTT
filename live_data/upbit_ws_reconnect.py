from __future__ import annotations

import time


def backoff_sleep(attempt: int, base_seconds: float = 1.0, max_seconds: float = 10.0) -> float:
    sleep_for = min(max_seconds, base_seconds * (2 ** max(0, attempt - 1)))
    time.sleep(sleep_for)
    return sleep_for
