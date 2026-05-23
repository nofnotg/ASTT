from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from execution.realistic_paper_account import RealisticPaperAccount
from execution.realistic_paper_fill_model import simulate_entry_fill, simulate_exit_fill
from execution.realistic_paper_ledger import RealisticPaperLedger
from execution.realistic_paper_order import build_paper_order
from execution.realistic_paper_position_manager import manage_open_position
from features.ema_pullback_candidate import detect_ema_pullback_candidate
from features.micro_candidate_sources import detect_micro_acceleration_candidate
from features.micro_feature_snapshot import build_micro_feature_snapshot
from features.micro_momentum_breakdown import breakdown_micro_momentum
from features.micro_target_space import compute_micro_target_space
from features.orderbook_imbalance_candidate import detect_orderbook_imbalance_candidate
from features.vwap_reclaim_candidate import detect_vwap_reclaim_candidate
from live_data.upbit_real_ws_session import run_upbit_real_ws_session
from replay_lab.paths import REPLAY_STORE_DIR


def run_realistic_paper_session_v555(duration_minutes: int = 60, top_markets: int = 20, initial_cash_krw: float = 500000, fixed_order_krw: float = 10000, strategies: list[str] | None = None, scenario: str = "realistic_1") -> dict:
    strategies = strategies or ["MICRO_ACCELERATION", "VWAP_RECLAIM", "EMA_PULLBACK", "ORDERBOOK_IMBALANCE"]
    markets = _default_markets(top_markets)
    source_session = run_upbit_real_ws_session(markets, duration_seconds=duration_minutes * 60, include_trade=True, include_orderbook=True)
    session_id = datetime.utcnow().strftime("realistic_paper_%Y%m%d_%H%M%S")
    session_dir = REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555" / session_id
    ledger = RealisticPaperLedger(session_dir)
    account = RealisticPaperAccount(initial_cash_krw=initial_cash_krw, fixed_order_krw=fixed_order_krw)
    trades, orderbooks = _load_events(source_session["session_id"])
    snapshots = _snapshots(markets, trades, orderbooks, session_id)
    candidate_count = enter_count = wait_count = cancel_count = 0
    weak_reasons = Counter()
    source_counts = Counter()
    source_enter_counts = Counter()
    source_wait_counts = Counter()
    source_cancel_counts = Counter()
    for snapshot in snapshots:
        ledger.append("SNAPSHOT", snapshot)
        candidates = _candidates(snapshot, strategies)
        if not candidates:
            weak = breakdown_micro_momentum(snapshot)
            weak_reasons.update(weak["weak_reasons"])
            continue
        for candidate in candidates:
            candidate_count += 1
            source_counts[candidate["candidate_source"]] += 1
            ledger.append("CANDIDATE", candidate)
            target = compute_micro_target_space(candidate, snapshot)
            if not target["tradable"]:
                wait_count += 1
                source_wait_counts[candidate["candidate_source"]] += 1
                ledger.append("GATE_REJECT", {**candidate, "reject_reason": target["reject_reason"]})
                continue
            if not account.can_open_position(fixed_order_krw):
                wait_count += 1
                source_wait_counts[candidate["candidate_source"]] += 1
                ledger.append("GATE_REJECT", {**candidate, "reject_reason": "MAX_OPEN_POSITION"})
                continue
            order = build_paper_order(candidate, fixed_order_krw)
            fill = simulate_entry_fill(candidate, snapshot, fixed_order_krw, scenario=scenario)
            if not fill["fill_possible"]:
                cancel_count += 1
                source_cancel_counts[candidate["candidate_source"]] += 1
                ledger.append("GATE_REJECT", {**candidate, "reject_reason": fill["reject_reason"]})
                continue
            enter_count += 1
            source_enter_counts[candidate["candidate_source"]] += 1
            ledger.append("PAPER_ORDER_SUBMITTED", order)
            position = account.open_position(order, fill)
            ledger.append("POSITION_OPENED", position)
            decision = manage_open_position(position, snapshot, {"max_hold_seconds": 0})
            exit_fill = simulate_exit_fill(position, snapshot, decision["decision"], scenario=scenario)
            closed = account.close_position(position["position_id"], exit_fill, decision["decision"])
            ledger.append("POSITION_CLOSED", closed)
    summary = _summary(
        session_id,
        duration_minutes,
        markets,
        source_session,
        account,
        candidate_count,
        enter_count,
        wait_count,
        cancel_count,
        source_counts,
        source_enter_counts,
        source_wait_counts,
        source_cancel_counts,
        weak_reasons,
        scenario,
        initial_cash_krw,
    )
    ledger.write_summary(summary)
    return summary


def _default_markets(top_markets: int) -> list[str]:
    base = ["KRW-BTC", "KRW-ETH", "KRW-SOL", "KRW-XRP", "KRW-DOGE", "KRW-ADA", "KRW-AVAX", "KRW-LINK", "KRW-SUI", "KRW-TRX"]
    return base[: max(1, min(top_markets, len(base)))]


def _load_events(source_session_id: str) -> tuple[list[dict], list[dict]]:
    roots = list((REPLAY_STORE_DIR / "raw" / "upbit_ws").glob(f"*/{source_session_id}"))
    trades, orderbooks = [], []
    if not roots:
        return trades, orderbooks
    root = roots[-1]
    for path in root.glob("trades/*.jsonl"):
        trades.extend(_read_jsonl(path, limit=800))
    for path in root.glob("orderbooks/*.jsonl"):
        orderbooks.extend(_read_jsonl(path, limit=800))
    return sorted(trades, key=lambda x: x.get("timestamp_ms", 0)), sorted(orderbooks, key=lambda x: x.get("timestamp_ms", 0))


def _read_jsonl(path: Path, limit: int) -> list[dict]:
    out = []
    with path.open(encoding="utf-8") as handle:
        for i, line in enumerate(handle):
            if i >= limit:
                break
            out.append(json.loads(line))
    return out


def _snapshots(markets: list[str], trades: list[dict], orderbooks: list[dict], session_id: str) -> list[dict]:
    snapshots = []
    for market in markets:
        market_trades = [event for event in trades if event.get("market") == market]
        if not market_trades:
            continue
        for event in market_trades[10:: max(1, len(market_trades) // 3 or 1)][:3]:
            snap = build_micro_feature_snapshot(market, int(event["timestamp_ms"]), trades, orderbooks)
            snap["session_id"] = session_id
            snapshots.append(snap)
    return snapshots


def _candidates(snapshot: dict, strategies: list[str]) -> list[dict]:
    minute = {"vwap": snapshot["last_price"] * 0.999, "previous_price": snapshot["last_price"] * 0.998, "ema20": snapshot["last_price"], "ema50": snapshot["last_price"] * 0.999}
    checks = {
        "MICRO_ACCELERATION": lambda: detect_micro_acceleration_candidate(snapshot),
        "VWAP_RECLAIM": lambda: detect_vwap_reclaim_candidate(snapshot["market"], snapshot, minute),
        "EMA_PULLBACK": lambda: detect_ema_pullback_candidate(snapshot["market"], snapshot, minute),
        "ORDERBOOK_IMBALANCE": lambda: detect_orderbook_imbalance_candidate(snapshot),
    }
    return [candidate for name in strategies if name in checks for candidate in [checks[name]()] if candidate]


def _summary(
    session_id,
    duration_minutes,
    markets,
    source_session,
    account,
    candidate_count,
    enter_count,
    wait_count,
    cancel_count,
    source_counts,
    source_enter_counts,
    source_wait_counts,
    source_cancel_counts,
    weak_reasons,
    scenario,
    initial_cash,
):
    wins = [p for p in account.closed_positions if p["pnl_krw"] > 0]
    losses = [p for p in account.closed_positions if p["pnl_krw"] <= 0]
    profit = sum(p["pnl_krw"] for p in wins)
    loss = abs(sum(p["pnl_krw"] for p in losses))
    trade_count = len(account.closed_positions)
    return {"session_id": session_id, "source_session_id": source_session["session_id"], "duration_minutes": duration_minutes, "markets": markets, "data_source": "UPBIT_WS", "initial_cash_krw": initial_cash, "final_equity_krw": account.equity_krw, "total_pnl_krw": account.realized_pnl_krw, "total_return_pct": account.realized_pnl_krw / initial_cash * 100 if initial_cash else 0.0, "candidate_count": candidate_count, "enter_count": enter_count, "wait_count": wait_count, "cancel_count": cancel_count, "trade_count": trade_count, "win_rate": len(wins) / trade_count if trade_count else 0.0, "profit_factor": profit / loss if loss else (999.0 if profit else 0.0), "expectancy_pct": sum(p["pnl_pct"] for p in account.closed_positions) / trade_count if trade_count else None, "max_drawdown_pct": account.max_drawdown_pct, "avg_hold_seconds": 0.0, "fee_total_krw": sum(p.get("entry_fee_krw", 0) + p.get("exit_fee_krw", 0) for p in account.closed_positions), "slippage_estimated_krw": 0.0, "source_counts": dict(source_counts), "source_enter_counts": dict(source_enter_counts), "source_wait_counts": dict(source_wait_counts), "source_cancel_counts": dict(source_cancel_counts), "weak_reason_counts": dict(weak_reasons), "scenario": scenario, "real_order_enabled": False, "live_readiness": "LIVE_NOT_ALLOWED", "trade_event_count": source_session.get("trade_event_count", 0), "orderbook_event_count": source_session.get("orderbook_event_count", 0)}
