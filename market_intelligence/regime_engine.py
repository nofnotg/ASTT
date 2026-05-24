from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from replay_lab.paths import REPLAY_STORE_DIR
from timing_lab.event_clip_store import read_jsonl


REGIMES = {"RISK_ON", "SELECTIVE_ALT", "BTC_DRAG", "CHOP", "NO_TRADE"}


def build_market_regime_v5r3(sessions_dir: str | Path = "replay_store/sessions") -> dict[str, Any]:
    clips = _clip_dirs()
    market_returns: dict[str, float] = {}
    market_volumes: dict[str, float] = {}
    for clip in clips:
        meta = _read(clip / "clip_meta.json")
        market = meta.get("market", "")
        trades = read_jsonl(clip / "trades.jsonl")
        if not market or len(trades) < 2:
            continue
        prices = [float(row.get("trade_price", 0.0)) for row in trades if float(row.get("trade_price", 0.0) or 0) > 0]
        if len(prices) < 2:
            continue
        market_returns[market] = (prices[-1] - prices[0]) / prices[0] * 100 if prices[0] else 0.0
        market_volumes[market] = sum(float(row.get("trade_volume", 0.0) or 0.0) * float(row.get("trade_price", 0.0) or 0.0) for row in trades)

    btc_return = market_returns.get("KRW-BTC", 0.0)
    up_count = sum(1 for value in market_returns.values() if value > 0)
    down_count = sum(1 for value in market_returns.values() if value <= 0)
    breadth = up_count / len(market_returns) if market_returns else 0.0
    top_volume = sorted(market_volumes.values(), reverse=True)
    volume_concentration = top_volume[0] / sum(top_volume) if top_volume and sum(top_volume) else 0.0
    event_counts = _latest_timing().get("events_by_type", {})

    regime = "CHOP"
    if not clips or len(market_returns) < 3:
        regime = "NO_TRADE"
    elif btc_return <= -0.5:
        regime = "BTC_DRAG"
    elif breadth >= 0.55 and btc_return >= -0.15:
        regime = "RISK_ON"
    elif breadth >= 0.35 and volume_concentration <= 0.35:
        regime = "SELECTIVE_ALT"

    long_allowed = regime not in {"NO_TRADE", "BTC_DRAG"}
    summary = {
        "schema_version": "v5r3",
        "regime": regime,
        "dominant_regime": regime,
        "regime_score": _score(regime, breadth, btc_return),
        "long_allowed": long_allowed,
        "btc_return_pct": btc_return,
        "breadth_up_count": up_count,
        "breadth_down_count": down_count,
        "breadth_ratio": breadth,
        "market_count": len(market_returns),
        "volume_concentration": volume_concentration,
        "event_counts": event_counts,
        "regime_distribution": dict(Counter([regime])),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "data_source": "TIMING_CLIPS_AND_REPORTS",
    }
    _write(REPLAY_STORE_DIR / "market_regime" / "latest_market_regime_summary.json", summary)
    _write(Path("docs/reports/latest_market_regime_summary.json"), summary)
    return summary


def _score(regime: str, breadth: float, btc_return: float) -> float:
    base = {"RISK_ON": 80, "SELECTIVE_ALT": 65, "CHOP": 45, "BTC_DRAG": 20, "NO_TRADE": 5}.get(regime, 0)
    return float(max(0.0, min(100.0, base + breadth * 10 + min(5.0, btc_return))))


def _clip_dirs() -> list[Path]:
    root = REPLAY_STORE_DIR / "timing_clips"
    return sorted(path.parent for path in root.glob("*/*/clip_meta.json"))


def _latest_timing() -> dict[str, Any]:
    return _read(Path("docs/reports/latest_timing_lab_summary.json"))


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
