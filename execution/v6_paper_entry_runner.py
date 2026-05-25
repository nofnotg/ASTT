from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from execution.v6_exit_manager import choose_v6_exit
from execution.v6_paper_broker import V6PaperBroker
from execution.v6_position_manager import summarize_v6_trades
from market_data.ohlcv_store import OHLCVStore
from risk.risk_position_sizer import size_position
from strategy_engine.mtf_volume_ict_strategy import build_v6_strategy_setups


def run_v6_strategy_backtest(
    strategy: str,
    months: int = 12,
    initial_cash_krw: float = 500000,
    paper_entry_policy: str = "ACTIVE_RESEARCH",
    store: OHLCVStore | None = None,
) -> dict[str, Any]:
    store = store or OHLCVStore()
    setup_summary = build_v6_strategy_setups(strategy, store)
    broker = V6PaperBroker(initial_cash_krw)
    paper_zero_reasons = Counter()
    for setup in setup_summary["setups"]:
        if paper_entry_policy != "ACTIVE_RESEARCH":
            paper_zero_reasons.update(["PAPER_POLICY_INACTIVE"])
            continue
        if float(setup.get("setup_quality_score", 0.0)) < 45:
            paper_zero_reasons.update(["SETUP_QUALITY_TOO_LOW"])
            continue
        if float(setup.get("risk_reward_ratio", 0.0)) < 1.2:
            paper_zero_reasons.update(["RISK_REWARD_TOO_LOW"])
            continue
        sizing = size_position(initial_cash_krw, setup["entry_price"], setup["stop_price"])
        if not sizing["sizing_valid"]:
            paper_zero_reasons.update([sizing["reason"] or "SIZING_INVALID"])
            continue
        frame = store.load("1h", setup["market"])
        if frame.empty:
            paper_zero_reasons.update(["OHLCV_DATA_MISSING"])
            continue
        setup = {**setup, "risk_amount_krw": sizing["risk_amount_krw"], "entry_time": str(frame["time"].iloc[max(0, len(frame) - 12)])}
        exit_plan = choose_v6_exit(frame.tail(12), setup)
        broker.execute_round_trip(setup, sizing["position_krw"], exit_plan["exit_price"], exit_plan["exit_time"], exit_plan["result"])
    summary = _summary(strategy, setup_summary, broker.trades, broker.max_drawdown_pct, initial_cash_krw, paper_entry_policy, paper_zero_reasons)
    name = strategy.lower().replace("_", "-")
    _write(Path(f"replay_store/v6_strategy/latest_{name}_summary.json"), summary)
    report_name = {
        "DADDY_VOLUME_NECKLINE": "latest_v6_daddy_strategy_summary.json",
        "ICT_FVG_OB_SWEEP": "latest_v6_ict_strategy_summary.json",
        "COMBINED_VOLUME_ICT": "latest_v6_combined_strategy_summary.json",
    }.get(strategy, f"latest_v6_{name}_summary.json")
    _write(Path("docs/reports") / report_name, summary)
    return summary


def _summary(strategy: str, setup_summary: dict, trades: list[dict], mdd: float, initial_cash: float, policy: str, zero_reasons: Counter) -> dict:
    perf = summarize_v6_trades(trades, initial_cash)
    by_setup = defaultdict(list)
    for trade in trades:
        by_setup[trade["setup_type"]].append(trade)
    setup_stats = {name: summarize_v6_trades(rows, initial_cash) for name, rows in by_setup.items()}
    return {
        "schema_version": "v6",
        "strategy": strategy,
        "paper_entry_policy": policy,
        "setup_count": setup_summary.get("setup_count", 0),
        **perf,
        "max_drawdown_pct": mdd,
        "weekly_return_avg": perf["total_return_pct"],
        "best_setup": max(setup_stats, key=lambda key: setup_stats[key]["expectancy_pct"]) if setup_stats else None,
        "worst_setup": min(setup_stats, key=lambda key: setup_stats[key]["expectancy_pct"]) if setup_stats else None,
        "setup_stats": setup_stats,
        "trades": trades,
        "paper_zero_reason": dict(zero_reasons) if not trades else {},
        "real_order_enabled": False,
        "live_order_allowed": False,
    }


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
