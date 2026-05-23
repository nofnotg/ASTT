from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LiveMicroConfig:
    duration_minutes: int = 60
    mode: str = "RECORD_AND_FORWARD_PAPER"
    static_markets: list[str] = field(default_factory=lambda: ["KRW-BTC", "KRW-ETH", "KRW-SOL"])
    dynamic_top_n: int = 20
    include_candidate_markets: bool = True
    trade_stream: bool = True
    orderbook_stream: bool = True
    flush_interval_seconds: int = 5
    forward_paper_enabled: bool = True
    fixed_order_krw: float = 10000.0
    max_positions: int = 1
    max_hold_seconds: int = 120
    entry_model: str = "MICRO_CONFIRM_ENTRY"
    exit_model: str = "MICRO_TP_AND_FAILURE_EXIT"
    fee_pct: float = 0.05
    slippage_pct: float = 0.05
    latency_ms: int = 500
    real_order_enabled: bool = False
    require_real_order_disabled: bool = True

    def validate(self) -> "LiveMicroConfig":
        if self.require_real_order_disabled and self.real_order_enabled:
            raise RuntimeError("real_order_enabled must remain false for V5.5.1")
        return self


def load_live_micro_config(path: str | Path | None = None, **overrides) -> LiveMicroConfig:
    data = {}
    if path:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        data = _flatten(data)
    data.update({k: v for k, v in overrides.items() if v is not None})
    return LiveMicroConfig(**{k: v for k, v in data.items() if k in LiveMicroConfig.__dataclass_fields__}).validate()


def _flatten(data: dict) -> dict:
    session = data.get("session", {})
    markets = data.get("markets", {})
    recording = data.get("recording", {})
    paper = data.get("forward_paper", {})
    cost = paper.get("cost_model", {})
    safety = data.get("safety", {})
    return {
        "duration_minutes": session.get("duration_minutes"),
        "mode": session.get("mode"),
        "static_markets": markets.get("static"),
        "dynamic_top_n": markets.get("dynamic_top_n"),
        "include_candidate_markets": markets.get("include_candidate_markets"),
        "trade_stream": recording.get("trade_stream"),
        "orderbook_stream": recording.get("orderbook_stream"),
        "flush_interval_seconds": recording.get("flush_interval_seconds"),
        "forward_paper_enabled": paper.get("enabled"),
        "fixed_order_krw": paper.get("fixed_order_krw"),
        "max_positions": paper.get("max_positions"),
        "max_hold_seconds": paper.get("max_hold_seconds"),
        "entry_model": paper.get("entry_model"),
        "exit_model": paper.get("exit_model"),
        "fee_pct": cost.get("fee_pct"),
        "slippage_pct": cost.get("slippage_pct"),
        "latency_ms": cost.get("latency_ms"),
        "real_order_enabled": safety.get("real_order_enabled"),
        "require_real_order_disabled": safety.get("require_real_order_disabled"),
    }
