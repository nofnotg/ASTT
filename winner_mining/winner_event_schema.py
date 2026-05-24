from __future__ import annotations

from uuid import uuid4


WINNER_RULES = {
    "MICRO_WINNER": {"min_seconds": 30, "max_seconds": 120, "return_pct": 0.35},
    "SCALP_WINNER": {"min_seconds": 180, "max_seconds": 300, "return_pct": 0.70},
    "MOMENTUM_WINNER": {"min_seconds": 300, "max_seconds": 900, "return_pct": 1.50},
    "SPIKE_WINNER": {"min_seconds": 0, "max_seconds": 900, "return_pct": 3.00},
}


def build_winner_event(market: str, winner_type: str, start: dict, peak: dict, source_data: str = "UPBIT_WS", quality: str = "GOOD", warnings=None) -> dict:
    start_price = float(start.get("price", start.get("trade_price", 0.0)))
    peak_price = float(peak.get("high", peak.get("price", peak.get("trade_price", 0.0))))
    start_ms = int(start.get("timestamp_ms", 0))
    peak_ms = int(peak.get("timestamp_ms", start_ms))
    return {
        "winner_id": f"{winner_type.lower()}_{market.replace('-', '').lower()}_{uuid4().hex[:10]}",
        "market": market,
        "winner_type": winner_type,
        "start_time_ms": start_ms,
        "peak_time_ms": peak_ms,
        "start_price": start_price,
        "peak_price": peak_price,
        "return_pct": (peak_price - start_price) / start_price * 100 if start_price else 0.0,
        "duration_seconds": max(0, int((peak_ms - start_ms) / 1000)),
        "source_data": source_data,
        "quality": quality,
        "warnings": warnings or [],
    }
