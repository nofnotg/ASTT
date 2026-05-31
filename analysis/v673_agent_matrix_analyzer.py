from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from analysis.v66_btcd_scenario_analyzer import load_true_walk_forward_journal
from btcd.btc_trend_feature_builder import BTCTrendFeatureStore
from btcd.btcdom_index_alignment import btcdom_lookahead_pass
from btcd.btcdom_index_data_quality import load_btcdom_index_quality
from btcd.btcdom_index_feature_builder import BTCDOMIndexFeatureStore
from btcd.btcdom_index_regime_classifier import classify_btcdom_market_state
from risk.risk_position_sizer import size_position


SCENARIOS = (
    "ROLLING_ONLY_CONTROL",
    "ROLLING_ONLY_DOMINANCE_OVERLAY",
    "BALANCED_ONLY_CONTROL",
    "BALANCED_ONLY_DOMINANCE_OVERLAY",
    "POLICY_BLEND_CONTROL",
    "POLICY_BLEND_DOMINANCE_OVERLAY",
    "RELATIVE_STRENGTH_BEAR_AGENT",
    "BEAR_DEFENSE_AGENT",
    "CASH_DEFENSE_AGENT",
    "BEAR_BOUNCE_V2_RESEARCH_AGENT",
    "SCENARIO_AGENT_ROUTER_V1",
)


def analyze_v673_agent_matrix(
    initial_cash_krw: float = 500000.0,
    reports_dir: str | Path = "docs/reports",
    archive_dir: str | Path = "replay_store/historical_archive",
    processed_dir: str | Path = "data/processed",
) -> dict[str, Any]:
    quality = _load_quality(reports_dir)
    if quality.get("data_quality") != "GOOD":
        scenarios = [_data_required_summary(name) for name in SCENARIOS]
        return _package(initial_cash_krw, quality, scenarios, [], [], [], _empty_audit(), [], {}, False)

    start = str(quality.get("common_coverage_start"))
    end = str(quality.get("common_coverage_end"))
    source = sorted(load_true_walk_forward_journal(reports_dir), key=lambda row: str(row.get("entry_time", "")))
    journal = [row for row in source if start <= str(row.get("entry_time", "")) <= end]
    store = BTCDOMIndexFeatureStore(processed_dir)
    btc_store = BTCTrendFeatureStore(archive_dir)

    contexts = _build_contexts(journal, store, btc_store)
    scenario_data = {name: _simulate_from_contexts(name, contexts, initial_cash_krw) for name in SCENARIOS}
    scenarios = [_summary(name, data, initial_cash_krw) for name, data in scenario_data.items()]
    saved = _saved_loss_missed_profit(scenario_data)
    scenarios = _decide(scenarios, saved)
    yearly = _yearly_comparison(scenario_data)
    market_state = _market_state_pnl(scenario_data["POLICY_BLEND_CONTROL"]["journal"])
    audit = _audit(scenario_data)
    router_journal = scenario_data["SCENARIO_AGENT_ROUTER_V1"]["journal"]
    period_records = _scenario_period_records(scenario_data)
    return _package(initial_cash_krw, quality, scenarios, saved, yearly, market_state, audit, router_journal, period_records, True)


def _build_contexts(
    source_journal: list[dict[str, Any]],
    store: BTCDOMIndexFeatureStore,
    btc_store: BTCTrendFeatureStore,
) -> list[dict[str, Any]]:
    contexts = []
    for trade in source_journal:
        decision_time = str(trade.get("feature_cutoff_time") or trade.get("signal_time") or trade.get("entry_time"))
        entry_time = str(trade.get("entry_time"))
        feature = store.feature_for(decision_time)
        btc = btc_store.feature_for(decision_time)
        state = _normalize_state(classify_btcdom_market_state(feature, btc))
        lookahead_pass = (
            _not_after(str(trade.get("feature_cutoff_time") or decision_time), decision_time)
            and _not_after(decision_time, entry_time)
            and btcdom_lookahead_pass(feature, decision_time)
            and _not_after(str(btc.get("timestamp")), decision_time)
        )
        contexts.append(
            {
                "trade": trade,
                "decision_time": decision_time,
                "entry_time": entry_time,
                "feature": feature,
                "btc": btc,
                "state": state,
                "selected_agent": _router_agent(state["market_state"]),
                "lookahead_pass": lookahead_pass,
            }
        )
    return contexts


def _simulate_from_contexts(
    scenario: str,
    contexts: list[dict[str, Any]],
    initial_cash: float,
) -> dict[str, Any]:
    equity = initial_cash
    peak = initial_cash
    rows: list[dict[str, Any]] = []
    for context in contexts:
        trade = context["trade"]
        decision_time = context["decision_time"]
        entry_time = context["entry_time"]
        feature = context["feature"]
        btc = context["btc"]
        state = context["state"]
        selected_agent = context["selected_agent"]
        action, multiplier, reasons = _action(scenario, trade, state, selected_agent)

        sizing = size_position(equity, float(trade.get("entry_price", 0.0)), float(trade.get("stop_price", 0.0)))
        if not sizing.get("sizing_valid") and action == "ENTER":
            action = "SKIP"
            multiplier = 0.0
            reasons.append("INVALID_SIZING")
        before = equity
        position = 0.0
        pnl = 0.0
        if action == "ENTER":
            position = min(float(sizing["position_krw"]), equity) * multiplier
            pnl = _unit_pnl(trade, position)
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        lookahead_pass = bool(context["lookahead_pass"])
        rows.append(
            {
                "trade_id": trade.get("trade_id"),
                "date": entry_time[:10],
                "scenario": scenario,
                "selected_agent_before_trade": selected_agent if scenario == "SCENARIO_AGENT_ROUTER_V1" else scenario,
                "decision_time": decision_time,
                "entry_time": entry_time,
                "feature_cutoff_time": str(trade.get("feature_cutoff_time") or decision_time),
                "dominance_feature_time_1h": feature.get("btcdom_feature_time_1h"),
                "dominance_feature_time_4h": feature.get("btcdom_feature_time_4h"),
                "dominance_feature_time_1d": feature.get("btcdom_feature_time_1d"),
                "btc_trend_feature_time": btc.get("timestamp"),
                "market": trade.get("market"),
                "plan": trade.get("plan"),
                "strategy": trade.get("strategy"),
                "setup_type": trade.get("setup_type"),
                "position_krw": position,
                "pnl_krw": pnl,
                "equity_before": before,
                "equity_after": equity,
                "drawdown_pct": (equity / peak - 1.0) * 100.0 if peak else 0.0,
                "defense_action": action,
                "risk_multiplier_after_defense": multiplier if action == "ENTER" else 0.0,
                "defense_reasons": reasons,
                "dominance_regime": state.get("dominance_regime"),
                "market_state": state.get("market_state"),
                "btc_trend": state.get("btc_trend"),
                "used_future_data": not lookahead_pass,
                "lookahead_check": "PASS" if lookahead_pass else "FAIL",
                "real_order_enabled": False,
                "live_order_allowed": False,
                "auto_apply_allowed": False,
            }
        )
    return {"journal": rows}


def _load_quality(reports_dir: str | Path) -> dict[str, Any]:
    v673 = Path(reports_dir) / "latest_v673_dominance_data_quality_summary.json"
    if v673.exists():
        import json

        return json.loads(v673.read_text(encoding="utf-8-sig"))
    return load_btcdom_index_quality(reports_dir)


def _simulate(
    scenario: str,
    source_journal: list[dict[str, Any]],
    initial_cash: float,
    store: BTCDOMIndexFeatureStore,
    btc_store: BTCTrendFeatureStore,
) -> dict[str, Any]:
    equity = initial_cash
    peak = initial_cash
    rows: list[dict[str, Any]] = []
    for trade in source_journal:
        decision_time = str(trade.get("feature_cutoff_time") or trade.get("signal_time") or trade.get("entry_time"))
        entry_time = str(trade.get("entry_time"))
        feature = store.feature_for(decision_time)
        btc = btc_store.feature_for(decision_time)
        state = _normalize_state(classify_btcdom_market_state(feature, btc))
        selected_agent = _router_agent(state["market_state"])
        action, multiplier, reasons = _action(scenario, trade, state, selected_agent)

        sizing = size_position(equity, float(trade.get("entry_price", 0.0)), float(trade.get("stop_price", 0.0)))
        if not sizing.get("sizing_valid") and action == "ENTER":
            action = "SKIP"
            multiplier = 0.0
            reasons.append("INVALID_SIZING")
        before = equity
        position = 0.0
        pnl = 0.0
        if action == "ENTER":
            position = min(float(sizing["position_krw"]), equity) * multiplier
            pnl = _unit_pnl(trade, position)
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        lookahead_pass = (
            _not_after(str(trade.get("feature_cutoff_time") or decision_time), decision_time)
            and _not_after(decision_time, entry_time)
            and btcdom_lookahead_pass(feature, decision_time)
            and _not_after(str(btc.get("timestamp")), decision_time)
        )
        rows.append(
            {
                "trade_id": trade.get("trade_id"),
                "date": entry_time[:10],
                "scenario": scenario,
                "selected_agent_before_trade": selected_agent if scenario == "SCENARIO_AGENT_ROUTER_V1" else scenario,
                "decision_time": decision_time,
                "entry_time": entry_time,
                "feature_cutoff_time": str(trade.get("feature_cutoff_time") or decision_time),
                "dominance_feature_time_1h": feature.get("btcdom_feature_time_1h"),
                "dominance_feature_time_4h": feature.get("btcdom_feature_time_4h"),
                "dominance_feature_time_1d": feature.get("btcdom_feature_time_1d"),
                "btc_trend_feature_time": btc.get("timestamp"),
                "market": trade.get("market"),
                "plan": trade.get("plan"),
                "strategy": trade.get("strategy"),
                "setup_type": trade.get("setup_type"),
                "position_krw": position,
                "pnl_krw": pnl,
                "equity_before": before,
                "equity_after": equity,
                "drawdown_pct": (equity / peak - 1.0) * 100.0 if peak else 0.0,
                "defense_action": action,
                "risk_multiplier_after_defense": multiplier if action == "ENTER" else 0.0,
                "defense_reasons": reasons,
                "dominance_regime": state.get("dominance_regime"),
                "market_state": state.get("market_state"),
                "btc_trend": state.get("btc_trend"),
                "used_future_data": not lookahead_pass,
                "lookahead_check": "PASS" if lookahead_pass else "FAIL",
                "real_order_enabled": False,
                "live_order_allowed": False,
                "auto_apply_allowed": False,
            }
        )
    return {"journal": rows}


def _normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    market_state = str(state.get("market_state") or "NORMAL")
    if market_state == "MARKET_WEAK_CASH_FLOW":
        market_state = "BEAR_DEFENSE"
    return {
        "market_state": market_state,
        "dominance_regime": state.get("btcdom_regime") or state.get("dominance_regime"),
        "btc_trend": state.get("btc_trend"),
    }


def _action(
    scenario: str,
    trade: dict[str, Any],
    state: dict[str, Any],
    selected_agent: str,
) -> tuple[str, float, list[str]]:
    if scenario == "SCENARIO_AGENT_ROUTER_V1":
        return _agent_action(selected_agent, trade, state)
    return _agent_action(scenario, trade, state)


def _agent_action(agent: str, trade: dict[str, Any], state: dict[str, Any]) -> tuple[str, float, list[str]]:
    market_state = str(state.get("market_state"))
    plan = str(trade.get("plan"))
    setup = str(trade.get("setup_type"))
    is_rolling = plan == "PLAN_A_ICT_FAT_TAIL"
    is_balanced = plan == "PLAN_B_COMBINED_CONTEXT"
    strong_setup = is_rolling or "FVG_OB_OVERLAP" in setup or "LIQUIDITY_SWEEP" in setup
    reasons = [market_state, str(state.get("dominance_regime"))]

    if agent == "OBSERVATION_ONLY":
        return "SKIP", 0.0, reasons + ["LOCKDOWN_OBSERVATION_ONLY"]
    if agent == "ROLLING_ONLY_CONTROL":
        return ("ENTER", 1.0, reasons + ["ROLLING_CONTROL"]) if is_rolling else ("SKIP", 0.0, reasons + ["NOT_ROLLING"])
    if agent == "BALANCED_ONLY_CONTROL":
        return ("ENTER", 1.0, reasons + ["BALANCED_CONTROL"]) if is_balanced else ("SKIP", 0.0, reasons + ["NOT_BALANCED"])
    if agent == "POLICY_BLEND_CONTROL":
        return "ENTER", 1.0, reasons + ["POLICY_BLEND_CONTROL"]

    if agent == "ROLLING_ONLY_DOMINANCE_OVERLAY":
        if not is_rolling:
            return "SKIP", 0.0, reasons + ["NOT_ROLLING"]
        return _dominance_overlay_action(reasons, market_state, strong_setup, plan_gate="ROLLING")
    if agent == "BALANCED_ONLY_DOMINANCE_OVERLAY":
        if not is_balanced:
            return "SKIP", 0.0, reasons + ["NOT_BALANCED"]
        return _dominance_overlay_action(reasons, market_state, strong_setup, plan_gate="BALANCED")
    if agent == "POLICY_BLEND_DOMINANCE_OVERLAY":
        if market_state == "BTC_LED_MARKET" and is_balanced:
            return "ENTER", 0.70, reasons + ["PLAN_B_BTC_LED_REDUCE"]
        return _dominance_overlay_action(reasons, market_state, strong_setup, plan_gate="POLICY")

    if agent == "RELATIVE_STRENGTH_BEAR_AGENT":
        if market_state in {"BTC_LED_MARKET", "RISK_OFF_ALT_WEAK"} and strong_setup:
            return "ENTER", 0.70, reasons + ["RELATIVE_STRENGTH_STRONG_ONLY"]
        if market_state in {"BTC_LED_MARKET", "RISK_OFF_ALT_WEAK"}:
            return "ENTER", 0.35, reasons + ["WEAK_ALT_REDUCE"]
        if market_state == "BEAR_DEFENSE":
            return "SKIP", 0.0, reasons + ["BEAR_DEFENSE_OBSERVATION"]
        return "ENTER", 1.0, reasons + ["PASS"]
    if agent == "BEAR_DEFENSE_AGENT":
        if market_state in {"RISK_OFF_ALT_WEAK", "BEAR_DEFENSE"} and not strong_setup:
            return "ENTER", 0.35, reasons + ["BEAR_DEFENSE_REDUCE_NON_A_PLUS"]
        if market_state in {"RISK_OFF_ALT_WEAK", "BEAR_DEFENSE"}:
            return "ENTER", 0.50, reasons + ["BEAR_DEFENSE_A_PLUS_LIMIT"]
        return "ENTER", 1.0, reasons + ["PASS"]
    if agent == "CASH_DEFENSE_AGENT":
        if market_state in {"BEAR_DEFENSE", "LOCKDOWN"}:
            return "SKIP", 0.0, reasons + ["CASH_DEFENSE"]
        return "ENTER", 0.35, reasons + ["CASH_DEFENSE_SMALL_SIZE"]
    if agent == "BEAR_BOUNCE_V2_RESEARCH_AGENT":
        return "SKIP", 0.0, reasons + ["RESEARCH_ONLY"]
    return "ENTER", 1.0, reasons + ["DEFAULT_PASS"]


def _dominance_overlay_action(reasons: list[str], market_state: str, strong_setup: bool, plan_gate: str) -> tuple[str, float, list[str]]:
    if market_state in {"ALT_FRIENDLY", "NORMAL"}:
        return "ENTER", 1.0, reasons + [f"{plan_gate}_DOM_ALLOW"]
    if market_state == "BTC_LED_MARKET":
        return "ENTER", 0.70, reasons + [f"{plan_gate}_BTC_LED_REDUCE"]
    if market_state == "RISK_OFF_ALT_WEAK":
        return "ENTER", 0.35, reasons + [f"{plan_gate}_RISK_OFF_REDUCE"]
    if market_state == "BEAR_DEFENSE" and strong_setup:
        return "ENTER", 0.35, reasons + [f"{plan_gate}_A_PLUS_ONLY"]
    if market_state in {"BEAR_DEFENSE", "LOCKDOWN"}:
        return "SKIP", 0.0, reasons + [f"{plan_gate}_OBSERVATION_ONLY"]
    return "ENTER", 1.0, reasons + [f"{plan_gate}_PASS"]


def _router_agent(market_state: str) -> str:
    if market_state in {"BULL_ATTACK", "ALT_FRIENDLY", "NORMAL"}:
        return "POLICY_BLEND_CONTROL"
    if market_state == "BTC_LED_MARKET":
        return "POLICY_BLEND_DOMINANCE_OVERLAY"
    if market_state == "EDGE_DECAY":
        return "RELATIVE_STRENGTH_BEAR_AGENT"
    if market_state == "RISK_OFF_ALT_WEAK":
        return "BEAR_DEFENSE_AGENT"
    if market_state == "BEAR_DEFENSE":
        return "CASH_DEFENSE_AGENT"
    if market_state == "BEAR_BOUNCE_ONLY":
        return "BEAR_BOUNCE_V2_RESEARCH_AGENT"
    if market_state == "LOCKDOWN":
        return "OBSERVATION_ONLY"
    return "POLICY_BLEND_CONTROL"


def _unit_pnl(trade: dict[str, Any], position_krw: float) -> float:
    entry = float(trade.get("entry_price", 0.0))
    exit_price = float(trade.get("exit_price", 0.0))
    if entry <= 0:
        return 0.0
    return position_krw * ((exit_price / entry) - 1.0) - position_krw * 0.001


def _not_after(left: str, right: str) -> bool:
    try:
        l = pd.Timestamp(left)
        r = pd.Timestamp(right)
        if l.tzinfo is None:
            l = l.tz_localize("UTC")
        else:
            l = l.tz_convert("UTC")
        if r.tzinfo is None:
            r = r.tz_localize("UTC")
        else:
            r = r.tz_convert("UTC")
        return l <= r
    except Exception:
        return False


def _summary(name: str, data: dict[str, Any], initial_cash: float) -> dict[str, Any]:
    rows = [row for row in data["journal"] if row["defense_action"] == "ENTER" and row["lookahead_check"] == "PASS"]
    pnls = [float(row["pnl_krw"]) for row in rows]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    final = float(data["journal"][-1]["equity_after"]) if data["journal"] else initial_cash
    ret = (final / initial_cash - 1.0) * 100.0 if initial_cash else 0.0
    mdd = min((float(row["drawdown_pct"]) for row in data["journal"]), default=0.0)
    gross_loss = abs(sum(losses))
    decisions = Counter(str(row.get("defense_action")) for row in data["journal"])
    agent_usage = Counter(str(row.get("selected_agent_before_trade")) for row in data["journal"])
    return {
        "scenario": name,
        "final_equity_krw": final,
        "total_return_pct": ret,
        "mdd_pct": mdd,
        "profit_factor": sum(wins) / gross_loss if gross_loss else 99.0 if wins else 0.0,
        "trade_count": len(rows),
        "skipped_trade_count": int(decisions.get("SKIP", 0)),
        "reduced_trade_count": sum(1 for row in rows if float(row.get("risk_multiplier_after_defense", 0.0)) < 1.0),
        "full_size_trade_count": sum(1 for row in rows if float(row.get("risk_multiplier_after_defense", 0.0)) >= 1.0),
        "average_position_size": sum(float(row.get("position_krw", 0.0)) for row in rows) / len(rows) if rows else 0.0,
        "return_mdd_ratio": ret / abs(mdd) if mdd else 0.0,
        "lookahead_fail_count": sum(1 for row in data["journal"] if row["lookahead_check"] != "PASS"),
        "agent_usage_count": dict(agent_usage),
        "decision": "PENDING",
    }


def _saved_loss_missed_profit(scenario_data: dict[str, Any]) -> list[dict[str, Any]]:
    control = {row["trade_id"]: row for row in scenario_data["POLICY_BLEND_CONTROL"]["journal"]}
    rows = []
    for scenario, data in scenario_data.items():
        if scenario == "POLICY_BLEND_CONTROL":
            continue
        saved = missed = 0.0
        for row in data["journal"]:
            control_pnl = float(control.get(row["trade_id"], {}).get("pnl_krw", 0.0))
            scenario_pnl = float(row.get("pnl_krw", 0.0))
            delta = scenario_pnl - control_pnl
            if control_pnl < 0 and delta > 0:
                saved += delta
            elif control_pnl > 0 and delta < 0:
                missed += -delta
        rows.append({"scenario": scenario, "saved_loss_krw": saved, "missed_profit_krw": missed, "net_effect_krw": saved - missed, "decision": "KEEP_CANDIDATE" if saved > missed else "REJECT"})
    return rows


def _decide(scenarios: list[dict[str, Any]], saved: list[dict[str, Any]]) -> list[dict[str, Any]]:
    control = next(row for row in scenarios if row["scenario"] == "POLICY_BLEND_CONTROL")
    saved_by = {row["scenario"]: row for row in saved}
    out = []
    for row in scenarios:
        item = dict(row)
        name = str(item["scenario"])
        if name == "POLICY_BLEND_CONTROL":
            item["decision"] = "BASELINE"
        elif name == "BEAR_BOUNCE_V2_RESEARCH_AGENT":
            item["decision"] = "RESEARCH_ONLY"
        elif item["lookahead_fail_count"]:
            item["decision"] = "DOMINANCE_FILTER_REJECTED"
        elif item["return_mdd_ratio"] > control["return_mdd_ratio"] and saved_by.get(name, {}).get("net_effect_krw", 0.0) >= 0:
            item["decision"] = _candidate_decision(name)
        else:
            item["decision"] = "DOMINANCE_FILTER_REJECTED"
        out.append(item)
    return out


def _candidate_decision(name: str) -> str:
    if name.startswith("ROLLING"):
        return "ROLLING_BTCDOM_CANDIDATE"
    if name.startswith("BALANCED"):
        return "BALANCED_BTCDOM_CANDIDATE"
    if name.startswith("POLICY"):
        return "POLICY_BLEND_BTCDOM_CANDIDATE"
    if name in {"RELATIVE_STRENGTH_BEAR_AGENT", "BEAR_DEFENSE_AGENT", "CASH_DEFENSE_AGENT"}:
        return "BEAR_AGENT_CANDIDATE"
    if name == "SCENARIO_AGENT_ROUTER_V1":
        return "SCENARIO_AGENT_ROUTER_CANDIDATE"
    return "DOMINANCE_FILTER_VALIDATED"


def _yearly_comparison(scenario_data: dict[str, Any]) -> list[dict[str, Any]]:
    control = {row["period"]: row for row in _period_rows(scenario_data["POLICY_BLEND_CONTROL"]["journal"])}
    names = [name for name in scenario_data if name != "POLICY_BLEND_CONTROL"]
    best = max(names, key=lambda name: _final_equity(scenario_data[name])) if names else "POLICY_BLEND_CONTROL"
    best_rows = {row["period"]: row for row in _period_rows(scenario_data[best]["journal"])}
    return [{"year": year, "control_return_pct": c["return_pct"], "best_v673_scenario": best, "best_v673_return_pct": best_rows.get(year, {}).get("return_pct", 0.0), "delta_pct_point": best_rows.get(year, {}).get("return_pct", 0.0) - c["return_pct"], "notes": "dominance coverage period only"} for year, c in control.items()]


def _period_rows(journal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        groups[str(row.get("date", ""))[:4]].append(row)
    rows = []
    for year, items in sorted(groups.items()):
        start = float(items[0]["equity_before"])
        end = float(items[-1]["equity_after"])
        rows.append({"period": year, "return_pct": (end / start - 1.0) * 100.0 if start else 0.0})
    return rows


def _scenario_period_records(scenario_data: dict[str, Any]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    return {
        name: {
            "daily": _aggregate_journal_periods(data["journal"], "day"),
            "weekly": _aggregate_journal_periods(data["journal"], "week"),
            "monthly": _aggregate_journal_periods(data["journal"], "month"),
        }
        for name, data in scenario_data.items()
    }


def _aggregate_journal_periods(journal: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        day = str(row.get("date", ""))[:10]
        if day:
            groups[_period_key(day, kind)].append(row)

    rows = []
    for period, items in sorted(groups.items()):
        start = float(items[0].get("equity_before", 0.0))
        end = float(items[-1].get("equity_after", 0.0))
        entered = [row for row in items if row.get("defense_action") == "ENTER" and row.get("lookahead_check") == "PASS"]
        wins = sum(1 for row in entered if float(row.get("pnl_krw", 0.0)) > 0)
        pnl = sum(float(row.get("pnl_krw", 0.0)) for row in items)
        mdd = min((float(row.get("drawdown_pct", 0.0)) for row in items), default=0.0)
        reduced = sum(1 for row in entered if float(row.get("risk_multiplier_after_defense", 0.0)) < 1.0)
        skipped = sum(1 for row in items if row.get("defense_action") == "SKIP")
        first_date = str(items[0].get("date", ""))[:10]
        last_date = str(items[-1].get("date", ""))[:10]
        rows.append(
            {
                "period": period,
                "date": period if kind == "day" else first_date,
                "start_date": first_date,
                "end_date": last_date,
                "trade_count": len(entered),
                "skipped_trade_count": skipped,
                "reduced_trade_count": reduced,
                "wins": wins,
                "win_rate": wins / len(entered) if entered else 0.0,
                "start_equity_krw": start,
                "end_equity_krw": end,
                "pnl_krw": pnl,
                "return_pct": (end / start - 1.0) * 100.0 if start else 0.0,
                "mdd_pct": mdd,
                "dominant_market_state": _most_common(items, "market_state"),
                "dominance_regime": _most_common(items, "dominance_regime"),
                "selected_agent": _most_common(items, "selected_agent_before_trade"),
            }
        )
    return rows


def _period_key(value: str, kind: str) -> str:
    y, m, d = [int(part) for part in value.split("-")]
    day = date(y, m, d)
    if kind == "day":
        return day.isoformat()
    if kind == "month":
        return f"{day.year:04d}-{day.month:02d}"
    iso = day.isocalendar()
    return f"{iso.year:04d}-W{iso.week:02d}"


def _most_common(rows: list[dict[str, Any]], key: str) -> str:
    counts = Counter(str(row.get(key) or "UNKNOWN") for row in rows)
    return counts.most_common(1)[0][0] if counts else "UNKNOWN"


def _final_equity(data: dict[str, Any]) -> float:
    return float(data["journal"][-1]["equity_after"]) if data["journal"] else 0.0


def _market_state_pnl(journal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        groups[str(row.get("market_state", "UNKNOWN"))].append(row)
    out = []
    for state, rows in sorted(groups.items()):
        pnl = sum(float(row.get("pnl_krw", 0.0)) for row in rows)
        out.append({"market_state": state, "pnl_krw": pnl, "trade_count": len(rows), "decision": "KEEP" if pnl >= 0 else "DEFENSE_REQUIRED"})
    return out


def _audit(scenario_data: dict[str, Any]) -> dict[str, Any]:
    total = sum(len(data["journal"]) for data in scenario_data.values())
    fails = sum(1 for data in scenario_data.values() for row in data["journal"] if row["lookahead_check"] != "PASS")
    return {"checked_trades": total, "pass": total - fails, "fail": fails, "excluded_trades": fails, "major_violations": [] if fails == 0 else ["Dominance/BTC feature timestamp after decision"]}


def _data_required_summary(name: str) -> dict[str, Any]:
    return {"scenario": name, "final_equity_krw": None, "total_return_pct": None, "mdd_pct": None, "profit_factor": None, "trade_count": 0, "return_mdd_ratio": None, "decision": "DOMINANCE_DATA_REQUIRED"}


def _empty_audit() -> dict[str, Any]:
    return {"checked_trades": 0, "pass": 0, "fail": 0, "excluded_trades": 0, "major_violations": ["DOMINANCE_DATA_REQUIRED"]}


def _package(
    initial_cash: float,
    quality: dict[str, Any],
    scenarios: list[dict[str, Any]],
    saved: list[dict[str, Any]],
    yearly: list[dict[str, Any]],
    market_state: list[dict[str, Any]],
    audit: dict[str, Any],
    router_journal: list[dict[str, Any]],
    period_records: dict[str, dict[str, list[dict[str, Any]]]],
    possible: bool,
) -> dict[str, Any]:
    return {
        "schema_version": "v673_agent_matrix_v2",
        "initial_cash_krw": initial_cash,
        "dominance_data_quality": quality,
        "coverage_period_validation_possible": possible,
        "reason": "Dominance data available." if possible else "Dominance data required.",
        "scenarios": scenarios,
        "saved_loss_missed_profit": saved,
        "yearly_comparison": yearly,
        "market_state_pnl": market_state,
        "lookahead_audit": audit,
        "router_journal": router_journal,
        "period_records": period_records,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
