from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from portfolio.compounding_engine import compound_trade_pnl, return_pct_from_equity
from strategy_router.strategy_router import plan_for_trade


def load_candidate_trades() -> list[dict[str, Any]]:
    paths = [
        Path("docs/reports/latest_v6_ict_strategy_summary.json"),
        Path("docs/reports/latest_v6_combined_strategy_summary.json"),
    ]
    trades: list[dict[str, Any]] = []
    for path in paths:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            trades.extend(payload.get("trades", []))
    return sorted(trades, key=lambda row: (str(row.get("entry_time")), row.get("strategy", ""), row.get("market", "")))


def simulate_equity_curve(initial_cash_krw: float = 500000, compounding: bool = True, max_open_positions: int = 3) -> dict[str, Any]:
    equity = initial_cash_krw
    peak = equity
    journal = []
    concurrent: dict[str, int] = {}
    for source in load_candidate_trades():
        route = plan_for_trade(source)
        if route["risk_multiplier"] <= 0:
            continue
        slot_key = str(source.get("entry_time"))
        concurrent[slot_key] = concurrent.get(slot_key, 0)
        if concurrent[slot_key] >= max_open_positions:
            continue
        concurrent[slot_key] += 1
        equity_before = equity
        pnl = compound_trade_pnl(float(source.get("pnl_krw", 0.0)), equity_before, initial_cash_krw) if compounding else float(source.get("pnl_krw", 0.0))
        equity_after = max(0.0, equity_before + pnl)
        peak = max(peak, equity_after)
        drawdown = (equity_after - peak) / peak * 100 if peak else 0.0
        journal.append({
            "trade_id": f"v62_{len(journal)+1:04d}",
            "source_trade_id": source.get("trade_id"),
            "date": str(source.get("entry_time", ""))[:10],
            "market": source.get("market"),
            "plan": route["plan"],
            "strategy": source.get("strategy"),
            "setup_type": source.get("setup_type"),
            "regime": route["regime"],
            "entry_time": source.get("entry_time"),
            "exit_time": source.get("exit_time"),
            "entry_price": source.get("entry_price"),
            "exit_price": source.get("exit_price"),
            "stop_price": source.get("stop_price"),
            "target_price": source.get("target_price"),
            "risk_per_trade_pct": 1.0 * route["risk_multiplier"],
            "risk_amount_krw": equity_before * 0.01 * route["risk_multiplier"],
            "position_krw": min(equity_before, float(source.get("position_krw", 0.0)) * (equity_before / initial_cash_krw)),
            "pnl_krw": pnl,
            "return_pct": return_pct_from_equity(pnl, equity_before),
            "equity_before": equity_before,
            "equity_after": equity_after,
            "drawdown_pct": drawdown,
            "result": source.get("result"),
            "entry_reason": route["reason"],
            "exit_reason": _exit_reason(source),
            "lesson": _lesson(source, pnl),
            "risk_flags": _risk_flags(source, route),
            "real_order_enabled": False,
            "live_order_allowed": False,
        })
        equity = equity_after
    return {
        "initial_cash_krw": initial_cash_krw,
        "final_equity_krw": equity,
        "total_return_pct": (equity - initial_cash_krw) / initial_cash_krw * 100 if initial_cash_krw else 0.0,
        "max_drawdown_pct": min((row["drawdown_pct"] for row in journal), default=0.0),
        "trade_count": len(journal),
        "journal": journal,
        "real_order_enabled": False,
        "live_order_allowed": False,
    }


def _exit_reason(trade: dict) -> str:
    result = trade.get("result")
    if result == "WIN":
        return "target_or_strong_follow_through"
    if result == "LOSS":
        return "stop_or_invalidated_setup"
    return "time_or_breakeven_exit"


def _lesson(trade: dict, pnl: float) -> str:
    if pnl > 0:
        return "규칙을 지킨 fat-tail 수익 거래입니다."
    return "손실이지만 stop/exit 규칙을 지킨 학습 거래입니다."


def _risk_flags(trade: dict, route: dict) -> list[str]:
    flags = ["OHLCV_ONLY_EXECUTION"]
    if route["regime"] == "HIGH_VOLATILITY":
        flags.append("HIGH_VOLATILITY")
    if trade.get("setup_type") == "FVG_OB_OVERLAP":
        flags.append("LOW_WIN_RATE_SETUP")
    return flags
