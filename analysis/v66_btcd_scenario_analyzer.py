from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from btcd.btcd_feature_builder import BTCDFeatureStore
from portfolio.causal_equity_defense_runner import _decide_multiplier, _drawdown
from portfolio.dynamic_risk_scaler import DynamicRiskScaler
from portfolio.profit_lock_engine import ProfitLockEngine
from portfolio.protected_floor_manager import ProtectedFloorManager
from risk.risk_position_sizer import size_position


SCENARIOS = [
    "CONTROL_EXISTING",
    "ROLLING_EDGE_BTCD_OVERLAY",
    "BALANCED_GROWTH_BTCD_OVERLAY",
    "POLICY_BLEND_BTCD_ROUTER",
    "BEAR_DEFENSE_BTCD",
    "BEAR_BOUNCE_BTCD",
    "RELATIVE_STRENGTH_BTCD",
    "SHORT_HEDGE_BTCD_RESEARCH",
    "HYBRID_BEAR_ROUTER_BTCD",
]


def analyze_v66_btcd_scenarios(
    journal: list[dict[str, Any]],
    initial_cash_krw: float = 500000.0,
    archive_dir: str | Path = "replay_store/historical_archive",
) -> dict[str, Any]:
    ordered = sorted(journal, key=lambda row: str(row.get("entry_time", "")))
    store = BTCDFeatureStore(archive_dir)
    scenario_data = {
        scenario: _simulate_scenario(scenario, ordered, store, initial_cash_krw)
        for scenario in SCENARIOS
    }
    scenarios = [_scenario_summary(name, data, initial_cash_krw) for name, data in scenario_data.items()]
    saved_rows = _saved_loss_missed_profit(scenario_data)
    scenarios = _relative_decisions(scenarios, saved_rows)
    return {
        "schema_version": "v66_btcd_scenario_lab_v1",
        "initial_cash_krw": initial_cash_krw,
        "data_quality": store.data_quality(),
        "scenarios": scenarios,
        "full_period": scenarios,
        "bear_focus_period": [_period_summary(name, data, "2024-11-01", initial_cash_krw) for name, data in scenario_data.items()],
        "saved_loss_missed_profit": saved_rows,
        "yearly_comparison": _yearly_comparison(scenario_data),
        "signal_effect": _signal_effect(scenario_data),
        "focus_2024_11": _focus_period_rows(scenario_data, "2024-11-01"),
        "short_research": _short_research_summary(scenario_data["SHORT_HEDGE_BTCD_RESEARCH"], initial_cash_krw),
        "audit": _audit(scenario_data),
        "equity_curve": {name: _sample(data["equity_curve"]) for name, data in scenario_data.items()},
        "drawdown_curve": {name: _sample(data["drawdown_curve"]) for name, data in scenario_data.items()},
        "btcd_curve": _btcd_curve_from_journal(ordered, store),
        "recommendation": _recommendation(scenarios, saved_rows),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def _simulate_scenario(
    scenario: str,
    source_journal: list[dict[str, Any]],
    store: BTCDFeatureStore,
    initial_cash: float,
) -> dict[str, Any]:
    equity = initial_cash
    peak = initial_cash
    scaler = DynamicRiskScaler()
    profit_lock = ProfitLockEngine(initial_cash)
    floor_manager = ProtectedFloorManager()
    rows: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []
    drawdown_curve: list[dict[str, Any]] = []
    action_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    current_month = ""
    month_start_equity = initial_cash

    for idx, trade in enumerate(source_journal):
        decision_time = str(trade.get("feature_cutoff_time") or trade.get("signal_time") or trade.get("entry_time"))
        entry_time = str(trade.get("entry_time"))
        month = entry_time[:7]
        if month != current_month:
            current_month = month
            month_start_equity = equity
        monthly_return = (equity / month_start_equity - 1.0) * 100.0 if month_start_equity else 0.0
        drawdown_before = _drawdown(equity, peak)
        rolling_audit = scaler.audit_window(20)
        pf = float(rolling_audit.get("rolling_profit_factor", 99.0))
        feature = store.feature_for(decision_time, pf, drawdown_before, monthly_return)
        base_policy = _base_policy(scenario, trade)
        base_decision = _decide_multiplier(base_policy, trade, equity, drawdown_before, scaler, profit_lock)
        multiplier = float(base_decision.get("risk_multiplier_after_defense", 1.0))
        action = "ENTER" if multiplier > 0 else "SKIP"
        reasons = list(base_decision.get("defense_reasons") or ["NO_DEFENSE"])
        action, multiplier, overlay_reasons = _apply_btcd_overlay(scenario, trade, feature, action, multiplier, pf, monthly_return)
        reasons.extend(overlay_reasons)

        sizing = size_position(equity, float(trade.get("entry_price", 0.0)), float(trade.get("stop_price", 0.0)))
        if not sizing.get("sizing_valid"):
            action = "SKIP"
            multiplier = 0.0
            reasons.append(str(sizing.get("reason") or "INVALID_SIZING"))

        position_krw = 0.0
        pnl = 0.0
        if action == "ENTER":
            base_position = min(float(sizing["position_krw"]), equity)
            unit_full = _unit_pnl(trade, base_position)
            floor_multiplier, floor_capped = floor_manager.cap_multiplier(equity, unit_full, multiplier)
            if floor_capped:
                multiplier = floor_multiplier
                reasons.append("PROTECTED_FLOOR_CAP")
            position_krw = base_position * multiplier
            pnl = _unit_pnl(trade, position_krw)
            if scenario == "SHORT_HEDGE_BTCD_RESEARCH":
                pnl = _short_proxy_pnl(trade, position_krw, feature)
            scaler.record(pnl, str(trade.get("exit_time")))

        equity_before = equity
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        drawdown_after = _drawdown(equity, peak)
        feature_cutoff_time = str(trade.get("feature_cutoff_time") or decision_time)
        btcd_feature_time = feature.upbit_flow.timestamp if feature.upbit_flow.source != "unavailable" else feature.global_btcd.timestamp
        lookahead_pass = feature_cutoff_time <= decision_time <= entry_time and str(btcd_feature_time) <= decision_time and feature.lookahead_check == "PASS"
        for reason in reasons:
            reason_counts[reason] += 1
        action_counts[action] += 1
        row = {
            "trade_id": trade.get("trade_id"),
            "date": entry_time[:10],
            "scenario": scenario,
            "entry_time": entry_time,
            "exit_time": trade.get("exit_time"),
            "decision_time": decision_time,
            "feature_cutoff_time": feature_cutoff_time,
            "btcd_feature_time": btcd_feature_time,
            "market": trade.get("market"),
            "plan": trade.get("plan"),
            "strategy": trade.get("strategy"),
            "setup_type": trade.get("setup_type"),
            "entry_price": float(trade.get("entry_price", 0.0)),
            "exit_price": float(trade.get("exit_price", 0.0)),
            "stop_price": float(trade.get("stop_price", 0.0)),
            "position_krw": position_krw,
            "pnl_krw": pnl,
            "return_pct": pnl / equity_before * 100.0 if equity_before else 0.0,
            "equity_before": equity_before,
            "equity_after": equity,
            "drawdown_pct": drawdown_after,
            "defense_action": action,
            "risk_multiplier_after_defense": 0.0 if action != "ENTER" else multiplier,
            "defense_reasons": reasons,
            "btcd_regime": feature.global_btcd.btcd_regime,
            "flow_regime": feature.upbit_flow.flow_regime,
            "bear_transition_score": feature.bear.bear_transition_score,
            "bear_state": feature.bear.bear_state,
            "alt_volume_breadth": feature.upbit_flow.alt_volume_breadth,
            "used_future_data": not lookahead_pass,
            "lookahead_check": "PASS" if lookahead_pass else "FAIL",
            "real_order_enabled": False,
            "live_order_allowed": False,
            "auto_apply_allowed": False,
        }
        rows.append(row)
        equity_curve.append({"sequence": idx, "time": trade.get("exit_time"), "equity": equity})
        drawdown_curve.append({"sequence": idx, "time": trade.get("exit_time"), "drawdown_pct": drawdown_after})

    return {
        "journal": rows,
        "equity_curve": equity_curve,
        "drawdown_curve": drawdown_curve,
        "action_counts": dict(action_counts),
        "reason_counts": dict(reason_counts),
    }


def _base_policy(scenario: str, trade: dict[str, Any]) -> str:
    if scenario in {"CONTROL_EXISTING", "BALANCED_GROWTH_BTCD_OVERLAY", "BEAR_DEFENSE_BTCD", "BEAR_BOUNCE_BTCD", "RELATIVE_STRENGTH_BTCD", "HYBRID_BEAR_ROUTER_BTCD"}:
        return "BALANCED_GROWTH"
    if scenario == "ROLLING_EDGE_BTCD_OVERLAY":
        return "ROLLING_EDGE_THROTTLE"
    if scenario == "POLICY_BLEND_BTCD_ROUTER":
        return "ROLLING_EDGE_THROTTLE" if str(trade.get("plan")) == "PLAN_A_ICT_FAT_TAIL" else "BALANCED_GROWTH"
    return "BALANCED_GROWTH"


def _apply_btcd_overlay(
    scenario: str,
    trade: dict[str, Any],
    feature: Any,
    action: str,
    multiplier: float,
    rolling_pf: float,
    monthly_return_pct: float,
) -> tuple[str, float, list[str]]:
    if scenario == "CONTROL_EXISTING":
        return action, multiplier, ["BTCD_NOT_USED_CONTROL"]
    flow = feature.upbit_flow.flow_regime
    btcd = feature.global_btcd.btcd_regime
    bear = feature.bear.bear_state
    score = feature.bear.bear_transition_score
    plan = str(trade.get("plan"))
    setup = str(trade.get("setup_type"))
    reasons: list[str] = [btcd, flow, bear]

    if scenario == "ROLLING_EDGE_BTCD_OVERLAY":
        if flow in {"BTC_FLOW_RISING", "BTC_FLOW_SPIKE"} and rolling_pf < 1.0:
            return action, min(multiplier, 0.35), reasons + ["ROLLING_BTCD_PF_WEAK_REDUCE"]
        if flow in {"BTC_FLOW_RISING", "BTC_FLOW_SPIKE"}:
            return action, min(multiplier, 0.70), reasons + ["ROLLING_BTCD_FLOW_RISK_REDUCE"]
        return action, multiplier, reasons + ["ROLLING_BTCD_PASS"]

    if scenario == "BALANCED_GROWTH_BTCD_OVERLAY":
        if flow == "BTC_FLOW_SPIKE" and monthly_return_pct < -3.0 and plan == "PLAN_B_COMBINED_CONTEXT":
            return "SKIP", 0.0, reasons + ["BALANCED_BTCD_PLAN_B_MONTHLY_LOSS_SKIP"]
        if flow in {"BTC_FLOW_RISING", "BTC_FLOW_SPIKE"} and plan == "PLAN_B_COMBINED_CONTEXT":
            return action, min(multiplier, 0.35), reasons + ["BALANCED_BTCD_PLAN_B_REDUCE"]
        return action, multiplier, reasons + ["BALANCED_BTCD_PASS"]

    if scenario == "POLICY_BLEND_BTCD_ROUTER":
        if score >= 75 and rolling_pf < 1.0:
            return "SKIP", 0.0, reasons + ["POLICY_BTCD_EDGE_DECAY_PLAN_C"]
        if plan == "PLAN_A_ICT_FAT_TAIL" and flow in {"BTC_FLOW_RISING", "BTC_FLOW_SPIKE"}:
            return action, min(multiplier, 0.70), reasons + ["PLAN_A_ROLLING_BTCD_REDUCE"]
        if plan == "PLAN_B_COMBINED_CONTEXT" and flow in {"BTC_FLOW_RISING", "BTC_FLOW_SPIKE"}:
            return action, min(multiplier, 0.35), reasons + ["PLAN_B_BALANCED_BTCD_REDUCE"]
        return action, multiplier, reasons + ["POLICY_BTCD_PASS"]

    if scenario == "BEAR_DEFENSE_BTCD":
        if score >= 90:
            return "SKIP", 0.0, reasons + ["BEAR_LOCKDOWN"]
        if score >= 75 and rolling_pf < 1.3:
            return "SKIP", 0.0, reasons + ["BEAR_DEFENSE_LONG_BLOCK"]
        if score >= 60:
            return action, min(multiplier, 0.35), reasons + ["BEAR_DEFENSE_REDUCE"]
        if score >= 35:
            return action, min(multiplier, 0.70), reasons + ["EDGE_DECAY_REDUCE"]
        return action, multiplier, reasons + ["BEAR_DEFENSE_PASS"]

    if scenario == "BEAR_BOUNCE_BTCD":
        if 60 <= score < 90 and ("LIQUIDITY_SWEEP" in setup or "FVG_OB_OVERLAP" in setup):
            return action, min(multiplier, 0.50), reasons + ["BEAR_BOUNCE_ONLY"]
        if score >= 60:
            return "SKIP", 0.0, reasons + ["BEAR_BOUNCE_SKIP_NON_BOUNCE"]
        return "SKIP", 0.0, reasons + ["BEAR_BOUNCE_NOT_ACTIVE"]

    if scenario == "RELATIVE_STRENGTH_BTCD":
        breadth = feature.upbit_flow.alt_volume_breadth
        relative_strength_like = plan == "PLAN_A_ICT_FAT_TAIL" and (breadth is not None and breadth >= 0.70)
        if score >= 60 and relative_strength_like:
            return action, min(multiplier, 0.70), reasons + ["RELATIVE_STRENGTH_ALLOW"]
        if score >= 60:
            return "SKIP", 0.0, reasons + ["RELATIVE_STRENGTH_BLOCK_WEAK_ALT"]
        return action, multiplier, reasons + ["RELATIVE_STRENGTH_NORMAL"]

    if scenario == "SHORT_HEDGE_BTCD_RESEARCH":
        if score >= 60 and flow in {"BTC_FLOW_RISING", "BTC_FLOW_SPIKE"}:
            return action, min(multiplier, 0.35), reasons + ["SHORT_RESEARCH_ONLY"]
        return "SKIP", 0.0, reasons + ["SHORT_RESEARCH_NO_SIGNAL"]

    if scenario == "HYBRID_BEAR_ROUTER_BTCD":
        if bear == "LOCKDOWN":
            return "SKIP", 0.0, reasons + ["HYBRID_LOCKDOWN_CASH_ONLY"]
        if bear == "BEAR_BOUNCE_ONLY":
            if "LIQUIDITY_SWEEP" in setup:
                return action, min(multiplier, 0.35), reasons + ["HYBRID_BEAR_BOUNCE_ONLY"]
            return "SKIP", 0.0, reasons + ["HYBRID_BEAR_BLOCK_LONG"]
        if bear == "BEAR_DEFENSE":
            if plan == "PLAN_A_ICT_FAT_TAIL" and rolling_pf > 1.2:
                return action, min(multiplier, 0.50), reasons + ["HYBRID_RELATIVE_PLAN_A"]
            return action, min(multiplier, 0.35), reasons + ["HYBRID_BEAR_DEFENSE_REDUCE"]
        if bear == "EDGE_DECAY":
            return action, min(multiplier, 0.70), reasons + ["HYBRID_EDGE_DECAY_REDUCE"]
        return action, multiplier, reasons + ["HYBRID_NORMAL"]

    return action, multiplier, reasons


def _unit_pnl(trade: dict[str, Any], position_krw: float) -> float:
    entry = float(trade.get("entry_price", 0.0))
    exit_price = float(trade.get("exit_price", 0.0))
    if entry <= 0:
        return 0.0
    return position_krw * ((exit_price / entry) - 1.0) - position_krw * 0.001


def _short_proxy_pnl(trade: dict[str, Any], position_krw: float, feature: Any) -> float:
    entry = float(trade.get("entry_price", 0.0))
    exit_price = float(trade.get("exit_price", 0.0))
    if entry <= 0:
        return 0.0
    raw = position_krw * ((entry / exit_price) - 1.0) if exit_price > 0 else 0.0
    hedge_factor = 0.45 if feature.bear.bear_transition_score >= 75 else 0.25
    return raw * hedge_factor - position_krw * 0.0015


def _scenario_summary(name: str, data: dict[str, Any], initial_cash: float) -> dict[str, Any]:
    entered = [row for row in data["journal"] if row["defense_action"] == "ENTER" and row["lookahead_check"] == "PASS"]
    pnls = [float(row["pnl_krw"]) for row in entered]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    final = float(data["journal"][-1]["equity_after"]) if data["journal"] else initial_cash
    ret = (final / initial_cash - 1.0) * 100.0 if initial_cash else 0.0
    mdd = min((float(row["drawdown_pct"]) for row in data["journal"]), default=0.0)
    gross_loss = abs(sum(losses))
    return {
        "scenario": name,
        "final_equity_krw": final,
        "total_return_pct": ret,
        "mdd_pct": mdd,
        "profit_factor": sum(wins) / gross_loss if gross_loss else 99.0 if wins else 0.0,
        "expectancy_pct": ((sum(pnls) / len(pnls)) / initial_cash * 100.0) if pnls else 0.0,
        "trade_count": len(entered),
        "skipped_trade_count": len(data["journal"]) - len(entered),
        "win_rate_pct": len(wins) / len(pnls) * 100.0 if pnls else 0.0,
        "return_mdd_ratio": ret / abs(mdd) if mdd else 0.0,
        "lookahead_fail_count": sum(1 for row in data["journal"] if row["lookahead_check"] != "PASS"),
        "decision": _scenario_decision(name, ret, mdd),
    }


def _scenario_decision(name: str, ret: float, mdd: float) -> str:
    if name == "SHORT_HEDGE_BTCD_RESEARCH":
        return "SHORT_RESEARCH_ONLY"
    if ret > 200 and mdd > -22:
        return "BEAR_ROUTER_CANDIDATE"
    if ret > 160 and mdd > -20:
        return "BTCD_FILTER_VALIDATED"
    if ret > 0 and mdd > -12:
        return "DEFENSIVE_BUT_RETURN_CUT"
    return "BTCD_FILTER_REJECTED"


def _relative_decisions(scenarios: list[dict[str, Any]], saved_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    control = next((row for row in scenarios if row["scenario"] == "CONTROL_EXISTING"), {})
    control_ratio = float(control.get("return_mdd_ratio", 0.0))
    control_return = float(control.get("total_return_pct", 0.0))
    net = {row["scenario"]: float(row.get("net_effect_krw", 0.0)) for row in saved_rows}
    adjusted = []
    for row in scenarios:
        item = dict(row)
        if item["scenario"] == "CONTROL_EXISTING":
            item["decision"] = "BASELINE"
        elif item["scenario"] == "SHORT_HEDGE_BTCD_RESEARCH":
            item["decision"] = "SHORT_RESEARCH_ONLY"
        elif item["scenario"] == "BEAR_BOUNCE_BTCD" and item["trade_count"] == 0:
            item["decision"] = "BTCD_FILTER_REJECTED"
        elif item["return_mdd_ratio"] > control_ratio and item["total_return_pct"] >= control_return * 0.98 and net.get(item["scenario"], 0.0) >= 0:
            item["decision"] = "BEAR_ROUTER_CANDIDATE"
        elif item["return_mdd_ratio"] > control_ratio and item["total_return_pct"] < control_return * 0.98:
            item["decision"] = "DEFENSIVE_BUT_RETURN_CUT"
        else:
            item["decision"] = "BTCD_FILTER_REJECTED"
        adjusted.append(item)
    return adjusted


def _period_summary(name: str, data: dict[str, Any], start_date: str, initial_cash: float) -> dict[str, Any]:
    rows = [row for row in data["journal"] if str(row.get("date")) >= start_date]
    if not rows:
        return {"scenario": name, "final_equity_krw": initial_cash, "total_return_pct": 0.0, "mdd_pct": 0.0, "profit_factor": 0.0, "trade_count": 0, "decision": "NO_DATA"}
    entered = [row for row in rows if row["defense_action"] == "ENTER"]
    start = float(rows[0]["equity_before"])
    end = float(rows[-1]["equity_after"])
    pnls = [float(row["pnl_krw"]) for row in entered]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_loss = abs(sum(losses))
    ret = (end / start - 1.0) * 100.0 if start else 0.0
    mdd = min(float(row["drawdown_pct"]) for row in rows)
    return {
        "scenario": name,
        "start_equity_krw": start,
        "final_equity_krw": end,
        "total_return_pct": ret,
        "mdd_pct": mdd,
        "profit_factor": sum(wins) / gross_loss if gross_loss else 99.0 if wins else 0.0,
        "trade_count": len(entered),
        "decision": _scenario_decision(name, ret, mdd),
    }


def _saved_loss_missed_profit(scenario_data: dict[str, Any]) -> list[dict[str, Any]]:
    control = {row["trade_id"]: row for row in scenario_data["CONTROL_EXISTING"]["journal"]}
    rows = []
    for scenario, data in scenario_data.items():
        if scenario == "CONTROL_EXISTING":
            continue
        skipped = [row for row in data["journal"] if row["defense_action"] != "ENTER"]
        saved = 0.0
        missed = 0.0
        for row in skipped:
            base = control.get(row["trade_id"], {})
            pnl = float(base.get("pnl_krw", 0.0))
            if pnl < 0:
                saved += -pnl
            elif pnl > 0:
                missed += pnl
        rows.append(
            {
                "scenario": scenario,
                "saved_loss_krw": saved,
                "missed_profit_krw": missed,
                "net_effect_krw": saved - missed,
                "skipped_trade_count": len(skipped),
                "decision": "KEEP_CANDIDATE" if saved > missed else "REJECT_OR_REDUCE",
            }
        )
    return rows


def _yearly_comparison(scenario_data: dict[str, Any]) -> list[dict[str, Any]]:
    control = {row["period"]: row for row in _period_rows(scenario_data["CONTROL_EXISTING"]["journal"], "year")}
    best_name = _best_scenario_name(scenario_data)
    best = {row["period"]: row for row in _period_rows(scenario_data[best_name]["journal"], "year")}
    rows = []
    for year, control_row in control.items():
        best_row = best.get(year, {})
        rows.append(
            {
                "year": year,
                "control_return_pct": control_row.get("return_pct", 0.0),
                "best_btcd_scenario": best_name,
                "best_btcd_return_pct": best_row.get("return_pct", 0.0),
                "delta_pct_point": best_row.get("return_pct", 0.0) - control_row.get("return_pct", 0.0),
                "notes": "BTCD overlay improved this year" if best_row.get("return_pct", 0.0) > control_row.get("return_pct", 0.0) else "Control was better or less damaged",
            }
        )
    return rows


def _signal_effect(scenario_data: dict[str, Any]) -> list[dict[str, Any]]:
    control = scenario_data["CONTROL_EXISTING"]["journal"]
    signals = ["BTCD_RISING", "BTCD_FALLING", "BTCD_SPIKE", "BTCD_BREAKDOWN", "BTC_FLOW_RISING", "BTC_FLOW_FALLING", "BTC_FLOW_SPIKE"]
    rows = []
    for signal in signals:
        affected = [
            row for row in control
            if row.get("btcd_regime") == signal or row.get("flow_regime") == signal or signal in row.get("defense_reasons", [])
        ]
        pnl = sum(float(row["pnl_krw"]) for row in affected if row["defense_action"] == "ENTER")
        rows.append(
            {
                "signal": signal,
                "trade_count": len([row for row in affected if row["defense_action"] == "ENTER"]),
                "effect_krw": pnl,
                "decision": "KEEP_AS_SOFT_WARNING" if pnl < 0 else "DO_NOT_HARD_BLOCK",
                "reason": "Negative control PnL near signal" if pnl < 0 else "Signal also contained profitable trades",
            }
        )
    return rows


def _focus_period_rows(scenario_data: dict[str, Any], start_date: str) -> list[dict[str, Any]]:
    return [_period_summary(name, data, start_date, 500000.0) for name, data in scenario_data.items()]


def _short_research_summary(data: dict[str, Any], initial_cash: float) -> dict[str, Any]:
    summary = _scenario_summary("SHORT_HEDGE_BTCD_RESEARCH", data, initial_cash)
    return {
        "short_research_return_pct": summary["total_return_pct"],
        "short_research_mdd_pct": summary["mdd_pct"],
        "hedge_effect_against_long_drawdown": "research proxy only; not connected to real exchange constraints",
        "major_risks": ["PAPER_ONLY", "1x proxy", "funding/slippage/regulatory constraints not modeled"],
        "decision": "SHORT_RESEARCH_ONLY",
    }


def _audit(scenario_data: dict[str, Any]) -> dict[str, Any]:
    total = sum(len(data["journal"]) for data in scenario_data.values())
    fails = sum(1 for data in scenario_data.values() for row in data["journal"] if row["lookahead_check"] != "PASS")
    return {
        "checked_trades": total,
        "pass": total - fails,
        "fail": fails,
        "excluded_trades": fails,
        "major_violations": [] if fails == 0 else ["BTCD feature time after decision time"],
    }


def _period_rows(journal: list[dict[str, Any]], period: str) -> list[dict[str, Any]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        groups[_period_key(str(row.get("date")), period)].append(row)
    rows = []
    for key, items in sorted(groups.items()):
        entered = [row for row in items if row["defense_action"] == "ENTER"]
        start = float(items[0]["equity_before"])
        end = float(items[-1]["equity_after"])
        pnls = [float(row["pnl_krw"]) for row in entered]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        gross_loss = abs(sum(losses))
        rows.append({
            "period": key,
            "start_equity": start,
            "end_equity": end,
            "return_pct": (end / start - 1.0) * 100.0 if start else 0.0,
            "trades": len(entered),
            "profit_factor": sum(wins) / gross_loss if gross_loss else 99.0 if wins else 0.0,
            "mdd_pct": min(float(row["drawdown_pct"]) for row in items),
        })
    return rows


def _period_key(date_text: str, period: str) -> str:
    dt = datetime.fromisoformat(date_text[:10])
    if period == "year":
        return str(dt.year)
    if period == "month":
        return f"{dt.year:04d}-{dt.month:02d}"
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year:04d}-W{iso_week:02d}"


def _best_scenario_name(scenario_data: dict[str, Any]) -> str:
    summaries = [_scenario_summary(name, data, 500000.0) for name, data in scenario_data.items()]
    return max(summaries, key=lambda row: row["return_mdd_ratio"]).get("scenario", "CONTROL_EXISTING")


def _btcd_curve_from_journal(journal: list[dict[str, Any]], store: BTCDFeatureStore) -> list[dict[str, Any]]:
    rows = []
    for idx, trade in enumerate(journal[:: max(1, len(journal) // 220) or 1]):
        decision_time = str(trade.get("feature_cutoff_time") or trade.get("entry_time"))
        feature = store.feature_for(decision_time)
        rows.append(
            {
                "sequence": idx,
                "time": decision_time,
                "global_btcd_pct": feature.global_btcd.btc_dominance_pct,
                "upbit_btc_flow_dominance_pct": feature.upbit_flow.upbit_btc_flow_dominance_pct,
                "bear_transition_score": feature.bear.bear_transition_score,
            }
        )
    return rows


def _recommendation(scenarios: list[dict[str, Any]], saved_rows: list[dict[str, Any]]) -> dict[str, Any]:
    control = next(row for row in scenarios if row["scenario"] == "CONTROL_EXISTING")
    candidates = [row for row in scenarios if row["scenario"] != "SHORT_HEDGE_BTCD_RESEARCH" and row["lookahead_fail_count"] == 0]
    best = max(candidates, key=lambda row: row["return_mdd_ratio"]) if candidates else control
    net = {row["scenario"]: row["net_effect_krw"] for row in saved_rows}
    if best["scenario"] != "CONTROL_EXISTING" and best["return_mdd_ratio"] > control["return_mdd_ratio"] and net.get(best["scenario"], -1.0) > 0:
        judgement = "BEAR_ROUTER_CANDIDATE"
    elif any(row["scenario"] != "CONTROL_EXISTING" and row["return_mdd_ratio"] > control["return_mdd_ratio"] for row in scenarios):
        judgement = "PAPER_MORE_REQUIRED"
    else:
        judgement = "BTCD_FILTER_REJECTED"
    return {
        "best_scenario": best["scenario"],
        "final_judgement": judgement,
        "forward_candidates": [best["scenario"]] if judgement in {"BEAR_ROUTER_CANDIDATE", "PAPER_MORE_REQUIRED"} else [],
        "research_only_candidates": ["SHORT_HEDGE_BTCD_RESEARCH"],
        "reason": "BTC Dominance overlay is accepted only if it improves return/MDD without excessive missed profit.",
    }


def _sample(rows: list[dict[str, Any]], target: int = 220) -> list[dict[str, Any]]:
    if len(rows) <= target:
        return rows
    step = max(1, len(rows) // target)
    sampled = rows[::step]
    return sampled + ([rows[-1]] if sampled[-1] != rows[-1] else [])


def load_true_walk_forward_journal(reports_dir: str | Path = "docs/reports") -> list[dict[str, Any]]:
    path = Path(reports_dir) / "latest_true_walk_forward_summary.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8-sig")).get("journal", [])
