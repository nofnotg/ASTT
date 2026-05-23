from __future__ import annotations

from live_data.upbit_ws_smoke_test import run_upbit_ws_smoke_test


def validate_upbit_real_ws(markets: list[str], duration_seconds: int = 300) -> dict:
    return run_upbit_ws_smoke_test(markets, duration_seconds)
