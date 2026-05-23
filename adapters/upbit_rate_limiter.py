from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class UpbitRateLimiter:
    max_calls_per_second: int = 8
    _calls: list[float] = field(default_factory=list)

    def wait(self) -> None:
        now = time.monotonic()
        self._calls = [ts for ts in self._calls if now - ts < 1.0]
        if len(self._calls) >= self.max_calls_per_second:
            sleep_for = 1.0 - (now - self._calls[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._calls.append(time.monotonic())
