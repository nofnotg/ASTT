import json
from pathlib import Path

from market_intelligence import regime_engine


def test_market_regime_v5r3_classifies_risk_on(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(regime_engine, "REPLAY_STORE_DIR", tmp_path / "replay_store")
    _clip(tmp_path, "s1", "btc", "KRW-BTC", [100.0, 101.0])
    _clip(tmp_path, "s1", "eth", "KRW-ETH", [100.0, 101.2])
    _clip(tmp_path, "s1", "xrp", "KRW-XRP", [100.0, 100.8])

    result = regime_engine.build_market_regime_v5r3(tmp_path / "replay_store" / "sessions")

    assert result["regime"] == "RISK_ON"
    assert result["long_allowed"] is True
    assert result["real_order_enabled"] is False


def _clip(root: Path, session: str, clip_id: str, market: str, prices: list[float]) -> None:
    clip_dir = root / "replay_store" / "timing_clips" / session / clip_id
    clip_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "clip_id": clip_id,
        "event_id": f"{clip_id}_event",
        "market": market,
        "event_type": "VOLUME_SPIKE",
        "event_time_ms": 1000,
        "quality": "GOOD",
    }
    (clip_dir / "clip_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    rows = [
        {"timestamp_ms": idx * 1000, "trade_price": price, "trade_volume": 100.0, "ask_bid": "BID"}
        for idx, price in enumerate(prices)
    ]
    (clip_dir / "trades.jsonl").write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
