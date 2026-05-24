import json
from pathlib import Path

from execution import aggressive_paper_learning_runner as runner


def test_aggressive_paper_learning_v5r3_enters_confirmed_setup_only_in_paper(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runner, "REPLAY_STORE_DIR", tmp_path / "replay_store")
    _clip(tmp_path)
    setup_dir = tmp_path / "replay_store" / "setup_candidates"
    setup_dir.mkdir(parents=True)
    candidate = {
        "candidate_id": "c1",
        "clip_id": "clip1",
        "event_id": "event1",
        "market": "KRW-ETH",
        "event_time_ms": 1000,
        "setup_type": "PULLBACK_RECLAIM",
        "setup_grade": "A",
        "regime": "RISK_ON",
        "risk_reward": 3.0,
        "target_space_pct": 1.0,
        "spread_pct": 0.02,
        "data_quality": "GOOD",
        "reject_reasons": [],
    }
    (setup_dir / "latest_setup_candidate_summary.json").write_text(json.dumps({"candidates": [candidate]}), encoding="utf-8")

    result = runner.run_aggressive_paper_learning_v5r3(initial_cash_krw=500000)

    assert result["paper_enter_count"] == 1
    assert result["trade_count"] == 1
    assert result["pnl_evaluable"] is True
    assert result["real_order_enabled"] is False


def _clip(root: Path) -> None:
    clip_dir = root / "replay_store" / "timing_clips" / "s1" / "clip1"
    clip_dir.mkdir(parents=True, exist_ok=True)
    meta = {"clip_id": "clip1", "event_id": "event1", "market": "KRW-ETH", "event_type": "ORDERFLOW_SHIFT", "event_time_ms": 1000}
    trades = [
        {"timestamp_ms": 1000, "trade_price": 100.0, "trade_volume": 1000.0, "ask_bid": "BID"},
        {"timestamp_ms": 2000, "trade_price": 101.0, "trade_volume": 1000.0, "ask_bid": "BID"},
    ]
    orderbook = {"timestamp_ms": 1000, "units": [{"ask_price": 100.0, "bid_price": 100.0, "ask_size": 10000.0}]}
    (clip_dir / "clip_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (clip_dir / "trades.jsonl").write_text("\n".join(json.dumps(row) for row in trades), encoding="utf-8")
    (clip_dir / "orderbooks.jsonl").write_text(json.dumps(orderbook), encoding="utf-8")
