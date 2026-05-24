import json
from pathlib import Path

from setup_intelligence import setup_engine


def test_setup_candidates_v5r3_builds_aggressive_setup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(setup_engine, "REPLAY_STORE_DIR", tmp_path / "replay_store")
    market_dir = tmp_path / "replay_store" / "market_regime"
    market_dir.mkdir(parents=True)
    (market_dir / "latest_market_regime_summary.json").write_text(
        json.dumps({"regime": "RISK_ON", "long_allowed": True}),
        encoding="utf-8",
    )
    _clip(tmp_path)

    result = setup_engine.build_setup_candidates_v5r3(initial_cash_krw=500000)

    assert result["candidate_count"] >= 1
    assert result["candidates"][0]["setup_type"] in setup_engine.SETUP_TYPES
    assert result["candidates"][0]["real_order_enabled"] is False


def _clip(root: Path) -> None:
    clip_dir = root / "replay_store" / "timing_clips" / "s1" / "clip1"
    clip_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "clip_id": "clip1",
        "event_id": "event1",
        "market": "KRW-ETH",
        "event_type": "ORDERFLOW_SHIFT",
        "event_time_ms": 2000,
        "quality": "GOOD",
    }
    trades = [
        {"timestamp_ms": 0, "trade_price": 100.0, "trade_volume": 3000.0, "ask_bid": "BID"},
        {"timestamp_ms": 1000, "trade_price": 100.4, "trade_volume": 3000.0, "ask_bid": "BID"},
        {"timestamp_ms": 2000, "trade_price": 100.8, "trade_volume": 3000.0, "ask_bid": "BID"},
    ]
    orderbook = {"timestamp_ms": 2000, "units": [{"ask_price": 100.85, "bid_price": 100.8, "ask_size": 10000.0}]}
    (clip_dir / "clip_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (clip_dir / "trades.jsonl").write_text("\n".join(json.dumps(row) for row in trades), encoding="utf-8")
    (clip_dir / "orderbooks.jsonl").write_text(json.dumps(orderbook), encoding="utf-8")
