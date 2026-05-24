from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from execution.realistic_paper_account import RealisticPaperAccount
from execution.realistic_paper_fill_model import simulate_entry_fill, simulate_exit_fill
from execution.risk_gate_v5 import evaluate_risk_gate_v5
from replay_lab.paths import REPLAY_STORE_DIR
from timing_lab.event_clip_store import read_jsonl


def run_aggressive_paper_learning_v5r3(
    duration_minutes: int = 60,
    top_markets: int = 30,
    initial_cash_krw: float = 500000,
    risk_profile: str = "aggressive",
    research_mode: bool = True,
) -> dict[str, Any]:
    setup = _read(REPLAY_STORE_DIR / "setup_candidates" / "latest_setup_candidate_summary.json")
    candidates = sorted(setup.get("candidates", []), key=lambda row: int(row.get("event_time_ms", 0) or 0))
    account = RealisticPaperAccount(initial_cash_krw=initial_cash_krw, fixed_order_krw=initial_cash_krw * 0.2)
    trades = []
    missed = 0
    missed_reasons: Counter[str] = Counter()
    false_entries = 0
    avoided_loss = 0
    consecutive_losses = 0
    daily_loss_limit_reached = False

    for candidate in candidates:
        if len({trade["market"] for trade in trades}) >= top_markets:
            break
        risk = _risk(candidate, daily_loss_limit_reached, consecutive_losses)
        if risk["veto"] or candidate.get("setup_grade") == "C":
            missed += 1
            missed_reasons.update(risk.get("veto_reasons") or ["GRADE_C"])
            if "REGIME_BLOCKED" in candidate.get("reject_reasons", []):
                avoided_loss += 1
            continue
        order_krw = min(account.cash_krw, initial_cash_krw * _allocation_pct(candidate) / 100)
        if order_krw < 5000 or not account.can_open_position(order_krw):
            missed += 1
            missed_reasons.update(["ACCOUNT_OR_MIN_ORDER_BLOCKED"])
            continue
        result = _paper_trade(candidate, order_krw, account)
        if not result.get("paper_entered"):
            missed += 1
            missed_reasons.update([str(result.get("reason") or "PAPER_ENTER_REJECTED")])
            continue
        trades.append(result)
        consecutive_losses = consecutive_losses + 1 if result["pnl_krw"] <= 0 else 0
        false_entries += 1 if result["pnl_krw"] <= 0 else 0
        if account.realized_pnl_krw <= initial_cash_krw * -0.03:
            daily_loss_limit_reached = True

    by_setup = _group_stats(trades, "setup_type")
    by_regime = _group_stats(trades, "regime")
    summary = {
        "schema_version": "v5r3",
        "risk_profile": risk_profile,
        "initial_cash_krw": float(initial_cash_krw),
        "final_equity_krw": account.equity_krw,
        "paper_enter_count": len(trades),
        "trade_count": len(trades),
        "win_count": sum(1 for row in trades if row["pnl_krw"] > 0),
        "loss_count": sum(1 for row in trades if row["pnl_krw"] <= 0),
        "win_rate": sum(1 for row in trades if row["pnl_krw"] > 0) / len(trades) if trades else None,
        "profit_factor": _profit_factor(trades),
        "expectancy_pct": sum(row["return_pct"] for row in trades) / len(trades) if trades else None,
        "total_pnl_krw": account.realized_pnl_krw,
        "total_return_pct": account.realized_pnl_krw / initial_cash_krw * 100 if initial_cash_krw else 0.0,
        "max_drawdown_pct": account.max_drawdown_pct,
        "pnl_evaluable": bool(trades),
        "realistic_1_status": "EVALUABLE" if trades else "N/A",
        "missed_entry_count": missed,
        "missed_reason_counts": dict(missed_reasons),
        "false_entry_count": false_entries,
        "avoided_loss_count": avoided_loss,
        "setup_performance": by_setup,
        "regime_performance": by_regime,
        "trades": trades,
        "research_mode": bool(research_mode),
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
    _write(REPLAY_STORE_DIR / "aggressive_paper" / "latest_aggressive_paper_learning_summary.json", summary)
    _write(Path("docs/reports/latest_aggressive_paper_learning_summary.json"), summary)
    return summary


def run_scenario_replay_v5r3(scenario_set: str | Path = "replay_store/scenarios", initial_cash_krw: float = 500000, risk_profile: str = "aggressive") -> dict[str, Any]:
    scenarios = _read(REPLAY_STORE_DIR / "scenarios" / "latest_scenario_set.json")
    paper = run_aggressive_paper_learning_v5r3(initial_cash_krw=initial_cash_krw, risk_profile=risk_profile)
    summary = {
        "schema_version": "v5r3",
        "scenario_count": scenarios.get("scenario_count", 0),
        "scenario_counts": scenarios.get("scenario_counts", {}),
        "by_scenario_type": scenarios.get("by_scenario_type", scenarios.get("scenario_counts", {})),
        "paper_enter_count": paper["paper_enter_count"],
        "trade_count": paper["trade_count"],
        "total_pnl_krw": paper["total_pnl_krw"],
        "total_return_pct": paper["total_return_pct"],
        "max_drawdown_pct": paper["max_drawdown_pct"],
        "missed_entry_count": paper["missed_entry_count"],
        "false_entry_count": paper["false_entry_count"],
        "avoided_loss_count": paper["avoided_loss_count"],
        "real_order_enabled": False,
    }
    _write(REPLAY_STORE_DIR / "scenarios" / "latest_scenario_replay_summary.json", summary)
    _write(Path("docs/reports/latest_scenario_replay_summary.json"), summary)
    return summary


def _paper_trade(candidate: dict[str, Any], order_krw: float, account: RealisticPaperAccount) -> dict[str, Any]:
    clip = _clip_dir(candidate.get("clip_id", ""))
    if not clip:
        return {"paper_entered": False, "reason": "CLIP_NOT_FOUND"}
    trades = read_jsonl(clip / "trades.jsonl")
    orderbooks = read_jsonl(clip / "orderbooks.jsonl")
    event_time = int(candidate.get("event_time_ms", 0) or 0)
    future = [row for row in trades if int(row.get("timestamp_ms", 0) or 0) >= event_time]
    if len(future) < 2:
        return {"paper_entered": False, "reason": "NO_FUTURE_TRADES"}
    entry_snapshot = _snapshot(future[0], orderbooks)
    entry_fill = simulate_entry_fill(candidate, entry_snapshot, order_krw, "realistic_1")
    if not entry_fill.get("fill_possible"):
        return {"paper_entered": False, "reason": entry_fill.get("reject_reason")}
    position = account.open_position({"market": candidate["market"], "order_krw": order_krw, "setup_type": candidate["setup_type"], "regime": candidate.get("regime")}, entry_fill)
    exit_row, reason = _choose_exit(future, entry_fill["fill_price"])
    exit_fill = simulate_exit_fill(position, _snapshot(exit_row, orderbooks), reason, "realistic_1")
    closed = account.close_position(position["position_id"], exit_fill, reason)
    return {
        "paper_entered": True,
        "market": candidate["market"],
        "clip_id": candidate.get("clip_id"),
        "setup_type": candidate["setup_type"],
        "setup_grade": candidate["setup_grade"],
        "regime": candidate.get("regime"),
        "entry_time_ms": int(future[0].get("timestamp_ms", 0) or 0),
        "exit_time_ms": int(exit_row.get("timestamp_ms", 0) or 0),
        "entry_price": entry_fill["fill_price"],
        "exit_price": exit_fill["fill_price"],
        "allocated_krw": order_krw,
        "pnl_krw": closed["pnl_krw"],
        "return_pct": closed["pnl_pct"],
        "exit_reason": reason,
        "real_order_enabled": False,
    }


def _choose_exit(future: list[dict[str, Any]], entry_price: float) -> tuple[dict[str, Any], str]:
    stop = entry_price * 0.9965
    target = entry_price * 1.006
    for row in future[1:]:
        price = float(row.get("trade_price", 0.0) or 0.0)
        if price >= target:
            return row, "TAKE_PROFIT"
        if price <= stop:
            return row, "STOP_LOSS"
    return future[-1], "TIME_STOP"


def _snapshot(trade: dict[str, Any], orderbooks: list[dict[str, Any]]) -> dict[str, Any]:
    price = float(trade.get("trade_price", 0.0) or 0.0)
    best_ask = price
    best_bid = price
    if orderbooks:
        units = orderbooks[0].get("units") or []
        if units:
            best_ask = float(units[0].get("ask_price", price) or price)
            best_bid = float(units[0].get("bid_price", price) or price)
    return {"last_price": price, "best_ask": best_ask, "best_bid": best_bid}


def _risk(candidate: dict[str, Any], daily_loss_limit_reached: bool, consecutive_losses: int) -> dict[str, Any]:
    payload = {
        **candidate,
        "regime": {"regime": candidate.get("regime"), "long_allowed": "REGIME_BLOCKED" not in candidate.get("reject_reasons", [])},
        "daily_loss_limit_reached": daily_loss_limit_reached,
        "consecutive_losses": consecutive_losses,
    }
    return evaluate_risk_gate_v5(payload, minimum_rr=1.1)


def _allocation_pct(candidate: dict[str, Any]) -> float:
    return {"B": 20.0, "A": 40.0, "S": 60.0}.get(candidate.get("setup_grade"), 0.0)


def _profit_factor(trades: list[dict[str, Any]]) -> float | None:
    if not trades:
        return None
    wins = sum(row["pnl_krw"] for row in trades if row["pnl_krw"] > 0)
    losses = abs(sum(row["pnl_krw"] for row in trades if row["pnl_krw"] <= 0))
    return float(wins / losses) if losses else None


def _group_stats(trades: list[dict[str, Any]], key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        groups[str(row.get(key, "UNKNOWN"))].append(row)
    return {
        name: {
            "trade_count": len(rows),
            "win_rate": sum(1 for row in rows if row["pnl_krw"] > 0) / len(rows),
            "total_pnl_krw": sum(row["pnl_krw"] for row in rows),
            "expectancy_pct": sum(row["return_pct"] for row in rows) / len(rows),
        }
        for name, rows in groups.items()
    }


def _clip_dir(clip_id: str) -> Path | None:
    if not clip_id:
        return None
    matches = list((REPLAY_STORE_DIR / "timing_clips").glob(f"*/*{clip_id}"))
    if matches:
        return matches[0]
    for meta in (REPLAY_STORE_DIR / "timing_clips").glob("*/*/clip_meta.json"):
        if _read(meta).get("clip_id") == clip_id:
            return meta.parent
    return None


def _read(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
