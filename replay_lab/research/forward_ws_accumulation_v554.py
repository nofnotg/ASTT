from __future__ import annotations

from execution.forward_ws_session_runner import run_forward_ws_session_v554


def run_forward_ws_accumulation_v554(duration_minutes: int = 60, top_markets: int = 20, priority_strategies: str | list[str] | None = None, fixed_order_krw: float = 10000) -> dict:
    if isinstance(priority_strategies, str):
        strategies = [item.strip() for item in priority_strategies.split(",") if item.strip()]
    else:
        strategies = priority_strategies
    return run_forward_ws_session_v554(duration_minutes=duration_minutes, top_markets=top_markets, priority_strategies=strategies, fixed_order_krw=fixed_order_krw)
