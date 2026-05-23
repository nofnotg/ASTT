from __future__ import annotations

from datetime import datetime


def build_candidate_event(session_id: str, market: str, reference_price: float, target_price: float | None = None, stop_price: float | None = None, setup_source: str = "v5_simple") -> dict:
    target = target_price or reference_price * 1.006
    stop = stop_price or reference_price * 0.994
    return {"session_id": session_id, "market": market, "candidate_time": datetime.utcnow().isoformat(), "setup_source": setup_source, "daily_state": "SIMULATED_FORWARD", "h4_state": "SIMULATED_FORWARD", "m5_trigger": "MICRO_DATA_READY", "reference_price": reference_price, "target_price": target, "stop_price": stop, "status": "SETUP_FOUND"}
