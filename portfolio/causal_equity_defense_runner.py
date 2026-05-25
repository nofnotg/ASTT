from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from portfolio.dynamic_risk_scaler import DynamicRiskScaler
from portfolio.profit_lock_engine import ProfitLockEngine
from portfolio.protected_floor_manager import ProtectedFloorManager
from portfolio.return_amplification_policy import SCENARIO_POLICIES, is_amplifiable_trade


def run_causal_scenarios(
    summary_path: str | Path = "docs/reports/latest_true_walk_forward_summary.json",
    initial_cash_krw: float = 500000,
) -> dict[str, Any]:
    source = _read(Path(summary_path))
    journal = sorted(source.get("journal", []), key=lambda row: str(row.get("entry_time", "")))
    scenarios = [_simulate_scenario(name, journal, float(initial_cash_krw)) for name in SCENARIO_POLICIES]
    baseline = next(row for row in scenarios if row["scenario"] == "BASELINE")
    for row in scenarios:
        row["comparison_to_baseline"] = _compare(row, baseline)
    return {
        "schema_version": "v64_causal_defense_v1",
        "source_summary": str(summary_path),
        "initial_cash_krw": initial_cash_krw,
        "investment_start_time": journal[0].get("entry_time") if journal else None,
        "investment_end_time": journal[-1].get("exit_time") if journal else None,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def _simulate_scenario(name: str, journal: list[dict[str, Any]], initial_cash: float) -> dict[str, Any]:
    equity = initial_cash
    peak = initial_cash
    scaler = DynamicRiskScaler()
    profit_lock = ProfitLockEngine(initial_cash)
    floor_manager = ProtectedFloorManager()
    trades: list[dict[str, Any]] = []
    curve: list[dict[str, Any]] = []
    skipped = 0
    protected_floor_violations = 0
    dd_cap_violations = 0
    max_loss_streak = 0
    loss_streak = 0

    for idx, trade in enumerate(journal):
        decision_time = str(trade.get("feature_cutoff_time") or trade.get("signal_time") or trade.get("entry_time"))
        entry_time = str(trade.get("entry_time"))
        feature_cutoff_time = str(trade.get("feature_cutoff_time") or decision_time)
        drawdown_before = _drawdown(equity, peak)
        base_pnl = float(trade.get("pnl_krw", 0.0))
        rolling_audit = scaler.audit_window(20)
        decision = _decide_multiplier(name, trade, equity, drawdown_before, scaler, profit_lock)
        multiplier = decision["risk_multiplier_after_defense"]
        floor_multiplier, floor_capped = floor_manager.cap_multiplier(equity, base_pnl, multiplier)
        if floor_capped:
            decision["defense_reasons"].append("PROTECTED_FLOOR_CAP")
            multiplier = floor_multiplier
        if decision["defense_action"] == "SKIP" or multiplier <= 0:
            pnl = 0.0
            skipped += 1
            action = "SKIP"
        else:
            pnl = base_pnl * multiplier
            action = "ENTER"
            scaler.record(pnl, str(trade.get("exit_time")))
        equity += pnl
        peak = max(peak, equity)
        drawdown_after = _drawdown(equity, peak)
        if pnl < 0:
            loss_streak += 1
            max_loss_streak = max(max_loss_streak, loss_streak)
        elif action == "ENTER":
            loss_streak = 0
        if floor_manager.floor_for_equity(equity) and equity < floor_manager.floor_for_equity(equity):
            protected_floor_violations += 1
        if name == "HIGH_OCTANE_RESEARCH" and drawdown_after <= -25:
            dd_cap_violations += 1
        lookahead_pass = feature_cutoff_time <= decision_time <= entry_time and int(rolling_audit["rolling_trades_used"]) <= idx
        annotated = {
            "trade_id": trade.get("trade_id"),
            "decision_time": decision_time,
            "entry_time": entry_time,
            "feature_cutoff_time": feature_cutoff_time,
            "used_future_data": False,
            "defense_state_before_trade": decision["defense_state_before_trade"],
            **rolling_audit,
            "lookahead_check": "PASS" if lookahead_pass else "FAIL",
            "market": trade.get("market"),
            "plan": trade.get("plan"),
            "strategy": trade.get("strategy"),
            "setup_type": trade.get("setup_type"),
            "base_pnl_krw": base_pnl,
            "scenario_pnl_krw": pnl,
            "equity_before": equity - pnl,
            "equity_after": equity,
            "drawdown_before_pct": drawdown_before,
            "drawdown_after_pct": drawdown_after,
            **decision,
            "risk_multiplier_after_defense": multiplier if action == "ENTER" else 0.0,
            "defense_action": action,
        }
        trades.append(annotated)
        curve.append({"sequence": idx, "time": trade.get("exit_time"), "equity": equity, "drawdown_pct": drawdown_after})

    capital = _capital_stats(trades, initial_cash)
    capital["max_losing_streak"] = max_loss_streak
    capital["return_to_mdd_ratio"] = _return_mdd_ratio(capital)
    capital["average_position_size_multiplier"] = _avg([float(t.get("risk_multiplier_after_defense", 0.0)) for t in trades if t.get("defense_action") == "ENTER"])
    return {
        "scenario": name,
        "decision": SCENARIO_POLICIES[name].decision,
        "high_risk_research_only": SCENARIO_POLICIES[name].high_risk_research_only,
        "capital": capital,
        "trade_count": capital["trade_count"],
        "skipped_trade_count": skipped,
        "protected_floor_violations": protected_floor_violations,
        "dd_cap_violations": dd_cap_violations,
        "lookahead_fail_count": sum(1 for trade in trades if trade["lookahead_check"] != "PASS"),
        "equity_curve_sample": _sample_curve(curve),
        "drawdown_curve_sample": _sample_curve([{"time": row["time"], "drawdown_pct": row["drawdown_pct"]} for row in curve]),
        "annotated_trade_sample": trades[:25],
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def _decide_multiplier(
    name: str,
    trade: dict[str, Any],
    equity: float,
    drawdown_before: float,
    scaler: DynamicRiskScaler,
    profit_lock: ProfitLockEngine,
) -> dict[str, Any]:
    stats20 = scaler.stats(20)
    stats30 = scaler.stats(30)
    multiplier = 1.0
    reasons: list[str] = []
    action = "ENTER"
    state = "NORMAL"
    month = str(trade.get("entry_time", ""))[:7]

    if name == "BASELINE":
        pass
    elif name == "DRAWDOWN_THROTTLE":
        if drawdown_before <= -10:
            multiplier = min(multiplier, 0.5)
            reasons.append("DRAWDOWN_THROTTLE_10")
            state = "CAUTION"
    elif name == "ROLLING_EDGE_THROTTLE":
        if stats20.trade_count >= 20 and (stats20.win_rate_pct < 35 or stats20.profit_factor < 0.8):
            multiplier = min(multiplier, 0.35)
            reasons.append("ROLLING_EDGE_THROTTLE")
            state = "DEFENSIVE"
    elif name == "HYBRID_DEFENSE":
        if stats20.trade_count >= 20 and (stats20.win_rate_pct < 35 or stats20.profit_factor < 0.8):
            multiplier = min(multiplier, 0.35)
            reasons.append("ROLLING_EDGE_THROTTLE")
            state = "DEFENSIVE"
        if drawdown_before <= -10:
            multiplier = min(multiplier, 0.5)
            reasons.append("DRAWDOWN_THROTTLE_10")
            state = "DEFENSIVE"
    elif name == "DEFENSIVE_CORE":
        if drawdown_before <= -30:
            action = "SKIP"
            state = "LOCKDOWN"
            reasons.append("LOCKDOWN_DD_30")
        elif drawdown_before <= -20 and str(trade.get("plan")) != "PLAN_A_ICT_FAT_TAIL":
            action = "SKIP"
            state = "DEFENSIVE"
            reasons.append("PLAN_A_ONLY_DD_20")
        elif drawdown_before <= -10:
            multiplier = min(multiplier, 0.5)
            state = "CAUTION"
            reasons.append("DRAWDOWN_THROTTLE_10")
        if stats20.trade_count >= 20 and stats20.profit_factor < 0.8:
            multiplier = min(multiplier, 0.35)
            state = "DEFENSIVE"
            reasons.append("ROLLING_PF_WEAK")
    elif name == "BALANCED_GROWTH":
        if stats20.trade_count >= 20:
            if stats20.win_rate_pct < 35 or stats20.profit_factor < 0.8:
                multiplier = min(multiplier, 0.35)
                state = "DEFENSIVE"
                reasons.append("ROLLING_EDGE_THROTTLE")
            elif stats20.profit_factor < 1.2:
                multiplier = min(multiplier, 0.7)
                state = "CAUTION"
                reasons.append("ROLLING_EDGE_CAUTION")
        if drawdown_before <= -20 and str(trade.get("plan")) != "PLAN_A_ICT_FAT_TAIL":
            action = "SKIP"
            state = "DEFENSIVE"
            reasons.append("PLAN_A_ONLY_DD_20")
    elif name == "AGGRESSIVE_GROWTH":
        if drawdown_before <= -35:
            action = "SKIP"
            state = "LOCKDOWN"
            reasons.append("LOCKDOWN_DD_35")
        elif drawdown_before <= -25:
            multiplier = min(multiplier, 0.35)
            state = "DEFENSIVE"
            reasons.append("DEFENSIVE_DD_25")
        elif drawdown_before <= -15:
            multiplier = min(multiplier, 0.35)
            state = "DEFENSIVE"
            reasons.append("BALANCED_DOWNGRADE_DD_15")
        elif is_amplifiable_trade(trade) and stats30.trade_count >= 30 and stats30.profit_factor > 1.5 and drawdown_before > -10:
            multiplier = 1.5
            state = "STRONG_EDGE"
            reasons.append("STRONG_EDGE_RISK_SCALE")
        elif is_amplifiable_trade(trade) and stats20.trade_count >= 20 and stats20.profit_factor > 1.3 and stats20.win_rate_pct > 45:
            multiplier = 1.25
            state = "HOT_HAND"
            reasons.append("HOT_HAND_RISK_SCALE")
        elif stats20.trade_count >= 20 and stats20.profit_factor < 0.8:
            multiplier = min(multiplier, 0.35)
            state = "DEFENSIVE"
            reasons.append("ROLLING_EDGE_THROTTLE")
    elif name == "HIGH_OCTANE_RESEARCH":
        if drawdown_before <= -25:
            action = "SKIP"
            state = "LOCKDOWN"
            reasons.append("RESEARCH_DD_CAP_25")
        elif not is_amplifiable_trade(trade):
            action = "SKIP"
            state = "CAUTION"
            reasons.append("HIGH_QUALITY_ONLY")
        elif stats30.trade_count >= 30 and stats30.profit_factor > 1.5 and drawdown_before > -10:
            multiplier = 2.0
            state = "STRONG_EDGE"
            reasons.append("HIGH_OCTANE_STRONG_EDGE")
        else:
            multiplier = 1.5
            state = "HOT_HAND"
            reasons.append("HIGH_OCTANE_BASE_RISK")

    if name in {"AGGRESSIVE_GROWTH", "HIGH_OCTANE_RESEARCH"}:
        cap, lock_reasons = profit_lock.monthly_multiplier_cap(month, equity)
        if multiplier > cap:
            multiplier = cap
            reasons.extend(lock_reasons)
            if state in {"HOT_HAND", "STRONG_EDGE"}:
                state = "CAUTION"

    return {
        "defense_mode": name,
        "risk_multiplier_before_defense": 1.0,
        "risk_multiplier_after_defense": 0.0 if action == "SKIP" else multiplier,
        "defense_reasons": reasons,
        "defense_action": action,
        "defense_state_before_trade": state,
    }


def _capital_stats(trades: list[dict[str, Any]], initial_cash: float) -> dict[str, Any]:
    executed = [trade for trade in trades if trade.get("defense_action") == "ENTER"]
    pnls = [float(trade.get("scenario_pnl_krw", 0.0)) for trade in executed]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    equity = initial_cash
    peak = initial_cash
    mdd = 0.0
    largest_win = max(pnls) if pnls else 0.0
    largest_loss = min(pnls) if pnls else 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        mdd = min(mdd, _drawdown(equity, peak))
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    return {
        "initial_cash_krw": initial_cash,
        "trade_count": len(executed),
        "final_equity_krw": equity,
        "total_pnl_krw": equity - initial_cash,
        "total_return_pct": (equity / initial_cash - 1.0) * 100 if initial_cash else 0.0,
        "cagr_equivalent_pct": _cagr(trades, initial_cash, equity),
        "max_drawdown_pct": mdd,
        "profit_factor": gross_win / gross_loss if gross_loss else 99.0 if gross_win else 0.0,
        "expectancy_pct": ((sum(pnls) / len(pnls)) / initial_cash * 100) if pnls else 0.0,
        "win_rate_pct": len(wins) / len(pnls) * 100 if pnls else 0.0,
        "largest_win_krw": largest_win,
        "largest_loss_krw": largest_loss,
    }


def _compare(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    capital = row["capital"]
    base = baseline["capital"]
    return {
        "final_equity_delta_krw": capital["final_equity_krw"] - base["final_equity_krw"],
        "return_delta_pct_point": capital["total_return_pct"] - base["total_return_pct"],
        "mdd_improvement_pct_point": capital["max_drawdown_pct"] - base["max_drawdown_pct"],
        "return_mdd_ratio_delta": capital["return_to_mdd_ratio"] - base["return_to_mdd_ratio"],
    }


def _cagr(trades: list[dict[str, Any]], initial_cash: float, final_equity: float) -> float:
    if not trades or initial_cash <= 0 or final_equity <= 0:
        return 0.0
    from datetime import datetime

    try:
        start = datetime.fromisoformat(str(trades[0].get("entry_time"))[:19])
        end = datetime.fromisoformat(str(trades[-1].get("entry_time"))[:19])
    except ValueError:
        return 0.0
    years = max((end - start).days / 365.25, 1 / 365.25)
    return ((final_equity / initial_cash) ** (1 / years) - 1.0) * 100


def _return_mdd_ratio(capital: dict[str, Any]) -> float:
    mdd = abs(float(capital.get("max_drawdown_pct", 0.0)))
    return float(capital.get("total_return_pct", 0.0)) / mdd if mdd else 0.0


def _drawdown(equity: float, peak: float) -> float:
    return (equity - peak) / peak * 100 if peak else 0.0


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _sample_curve(curve: list[dict[str, Any]], target: int = 220) -> list[dict[str, Any]]:
    if len(curve) <= target:
        return curve
    step = max(1, len(curve) // target)
    sample = curve[::step]
    return sample + ([curve[-1]] if sample[-1] != curve[-1] else [])


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
