from __future__ import annotations

import json
from pathlib import Path


def trade(ts: int, price: float, volume: float = 1.0, ask_bid: str = "BID", market: str = "KRW-TEST") -> dict:
    return {"type": "trade", "market": market, "timestamp_ms": ts, "trade_price": price, "trade_volume": volume, "ask_bid": ask_bid}


def orderbook(ts: int, ask: float = 100.0, bid: float = 99.9, ask_size: float = 10000.0, market: str = "KRW-TEST") -> dict:
    return {
        "type": "orderbook",
        "market": market,
        "timestamp_ms": ts,
        "units": [{"ask_price": ask, "bid_price": bid, "ask_size": ask_size, "bid_size": ask_size}],
    }


def make_clip(root: Path, prices: list[float] | None = None, quality: str = "GOOD") -> Path:
    prices = prices or [100.0, 100.2, 100.5]
    clip_dir = root / "s1" / "event1_clip"
    clip_dir.mkdir(parents=True)
    meta = {
        "clip_id": "event1_clip",
        "event_id": "event1",
        "market": "KRW-TEST",
        "event_type": "VOLUME_SPIKE",
        "event_time_ms": 1000,
        "quality": quality,
        "status": "CLOSED",
        "real_order_enabled": False,
    }
    (clip_dir / "clip_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (clip_dir / "trades.jsonl").write_text("\n".join(json.dumps(trade(1000 + i * 10000, p)) for i, p in enumerate(prices)), encoding="utf-8")
    (clip_dir / "orderbooks.jsonl").write_text("\n".join(json.dumps(orderbook(1000 + i * 10000)) for i in range(len(prices))), encoding="utf-8")
    (clip_dir / "tickers.jsonl").write_text("", encoding="utf-8")
    return clip_dir
