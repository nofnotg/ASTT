from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from analysis.v66_btcd_scenario_analyzer import load_true_walk_forward_journal
from btcd.btc_trend_feature_builder import BTCTrendFeatureStore
from btcd.btcd_market_regime_classifier import classify_btcd_market_regime
from btcd.global_btcd_feature_builder import GlobalBTCDHistoryFeatureStore
from btcd.global_btcd_history_loader import load_global_btcd_history
from risk.risk_position_sizer import size_position


GLOBAL_BTCD_SCENARIOS = [
    "CONTROL_EXISTING",
    "GLOBAL_BTCD_ALT_PERMISSION_FILTER",
    "GLOBAL_BTCD_RELATIVE_STRENGTH_FILTER",
    "GLOBAL_BTCD_BEAR_DEFENSE_FILTER",
    "GLOBAL_BTCD_COMPACT_ROUTER",
]


def analyze_v67_global_btcd_scenarios(
    journal: list[dict[str, Any]] | None = None,
    initial_cash_krw: float = 500000.0,
    reports_dir: str | Path = "docs/reports",
    archive_dir: str | Path = "replay_store/historical_archive",
    history_path: str | Path = "data/external/btc_dominance_history.csv",
) -> dict[str, Any]:
    source_journal = sorted(journal if journal is not None else load_true_walk_forward_journal(reports_dir), key=lambda row: str(row.get("entry_time", "")))
    history, history_quality = load_global_btcd_history(history_path)
    if history.empty:
        control = _control_from_existing_reports(reports_dir, initial_cash_krw)
        scenarios = [control] + [_data_required_summary(name) for name in GLOBAL_BTCD_SCENARIOS if name != "CONTROL_EXISTING"]
        return _package(initial_cash_krw, history_quality, scenarios, [], [], [], _empty_audit(), full_possible=False)

    btcd_store = GlobalBTCDHistoryFeatureStore(history_path)
    btc_store = BTCTrendFeatureStore(archive_dir)
    scenario_data = {scenario: _simulate(scenario, source_journal, initial_cash_krw, btcd_store, btc_store) for scenario in GLOBAL_BTCD_SCENARIOS}
    scenarios = [_summary(name, data, initial_cash_krw) for name, data in scenario_data.items()]
    saved = _saved_loss_missed_profit(scenario_data)
    scenarios = _reject_or_keep(scenarios, saved, history_quality)
    yearly = _yearly_comparison(scenario_data)
    regime = _regime_effect(scenario_data["CONTROL_EXISTING"]["journal"])
    audit = _audit(scenario_data)
    return _package(initial_cash_krw, history_quality, scenarios, saved, yearly, regime, audit, full_possible=True)


def _simulate(
    scenario: str,
    source_journal: list[dict[str, Any]],
    initial_cash: float,
    btcd_store: GlobalBTCDHistoryFeatureStore,
    btc_store: BTCTrendFeatureStore,
) -> dict[str, Any]:
    equity = initial_cash
    peak = initial_cash
    rows: list[dict[str, Any]] = []
    for trade in source_journal:
        decision_time = str(trade.get("feature_cutoff_time") or trade.get("signal_time") or trade.get("entry_time"))
        entry_time = str(trade.get("entry_time"))
        btcd = btcd_store.feature_for(decision_time)
        btc = btc_store.feature_for(decision_time)
        regime = classify_btcd_market_regime(btcd, btc)
        action, multiplier, reasons = _scenario_action(scenario, trade, regime, btcd)
        sizing = size_position(equity, float(trade.get("entry_price", 0.0)), float(trade.get("stop_price", 0.0)))
        if not sizing.get("sizing_valid"):
            action = "SKIP"
            multiplier = 0.0
            reasons.append("INVALID_SIZING")
        equity_before = equity
        position = 0.0
        pnl = 0.0
        if action == "ENTER":
            position = min(float(sizing["position_krw"]), equity) * multiplier
            pnl = _unit_pnl(trade, position)
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        btcd_time = str(btcd.get("timestamp"))
        btc_time = str(btc.get("timestamp"))
        lookahead_pass = str(trade.get("feature_cutoff_time") or decision_time) <= decision_time <= entry_time and btcd_time <= decision_time and btc_time <= decision_time
        rows.append(
            {
                "trade_id": trade.get("trade_id"),
                "date": entry_time[:10],
                "scenario": scenario,
                "decision_time": decision_time,
                "entry_time": entry_time,
                "feature_cutoff_time": str(trade.get("feature_cutoff_time") or decision_time),
                "btcd_feature_time": btcd_time,
                "btc_trend_feature_time": btc_time,
                "market": trade.get("market"),
                "plan": trade.get("plan"),
                "strategy": trade.get("strategy"),
                "setup_type": trade.get("setup_type"),
                "position_krw": position,
                "pnl_krw": pnl,
                "equity_before": equity_before,
                "equity_after": equity,
                "drawdown_pct": (equity / peak - 1.0) * 100.0 if peak else 0.0,
                "defense_action": action,
                "risk_multiplier_after_defense": multiplier if action == "ENTER" else 0.0,
                "defense_reasons": reasons,
                "btcd_regime": btcd.get("btcd_regime"),
                "btc_trend": btc.get("btc_price_trend_4h"),
                "market_regime": regime.get("market_regime"),
                "used_future_data": not lookahead_pass,
                "lookahead_check": "PASS" if lookahead_pass and btcd.get("lookahead_check") == "PASS" and btc.get("lookahead_check") == "PASS" else "FAIL",
                "real_order_enabled": False,
                "live_order_allowed": False,
                "auto_apply_allowed": False,
            }
        )
    return {"journal": rows}


def _scenario_action(scenario: str, trade: dict[str, Any], regime: dict[str, Any], btcd: dict[str, Any]) -> tuple[str, float, list[str]]:
    if scenario == "CONTROL_EXISTING":
        return "ENTER", 1.0, ["GLOBAL_BTCD_NOT_USED_CONTROL"]
    market_regime = str(regime.get("market_regime"))
    btcd_regime = str(btcd.get("btcd_regime"))
    plan = str(trade.get("plan"))
    setup = str(trade.get("setup_type"))
    reasons = [market_regime, btcd_regime]

    if scenario == "GLOBAL_BTCD_ALT_PERMISSION_FILTER":
        if market_regime == "ALT_FRIENDLY":
            return "ENTER", 1.0, reasons + ["ALT_FRIENDLY_ALLOW"]
        if market_regime == "BTC_LED_MARKET":
            return "ENTER", 0.70, reasons + ["BTC_LED_REDUCE"]
        if market_regime == "RISK_OFF_ALT_WEAK":
            return "ENTER", 0.35, reasons + ["RISK_OFF_REDUCE"]
        if market_regime == "MARKET_WEAK_CASH_FLOW":
            return "ENTER", 0.35, reasons + ["MARKET_WEAK_OBSERVATION_SIZE"]
        return "ENTER", 1.0, reasons + ["NEUTRAL_ALLOW"]

    if scenario == "GLOBAL_BTCD_RELATIVE_STRENGTH_FILTER":
        strong_setup = plan == "PLAN_A_ICT_FAT_TAIL" or "FVG_OB_OVERLAP" in setup or "LIQUIDITY_SWEEP" in setup
        if market_regime == "RISK_OFF_ALT_WEAK" and strong_setup:
            return "ENTER", 0.70, reasons + ["RELATIVE_STRENGTH_ONLY"]
        if market_regime == "RISK_OFF_ALT_WEAK":
            return "SKIP", 0.0, reasons + ["WEAK_ALT_BLOCK"]
        if market_regime == "MARKET_WEAK_CASH_FLOW" and strong_setup:
            return "ENTER", 0.35, reasons + ["A_PLUS_WEAK_MARKET_SMALL_SIZE"]
        if market_regime == "MARKET_WEAK_CASH_FLOW":
            return "SKIP", 0.0, reasons + ["OBSERVATION_ONLY"]
        return "ENTER", 1.0, reasons + ["RELATIVE_STRENGTH_PASS"]

    if scenario == "GLOBAL_BTCD_BEAR_DEFENSE_FILTER":
        weak = market_regime in {"RISK_OFF_ALT_WEAK", "MARKET_WEAK_CASH_FLOW"}
        if weak and plan != "PLAN_A_ICT_FAT_TAIL":
            return "ENTER", 0.35, reasons + ["BEAR_DEFENSE_REDUCE_NON_A_PLUS"]
        if weak:
            return "ENTER", 0.50, reasons + ["BEAR_DEFENSE_A_PLUS_LIMIT"]
        return "ENTER", 1.0, reasons + ["BEAR_DEFENSE_PASS"]

    if scenario == "GLOBAL_BTCD_COMPACT_ROUTER":
        if market_regime == "ALT_FRIENDLY":
            return "ENTER", 1.0, reasons + ["COMPACT_ALT_FRIENDLY"]
        if market_regime == "BTC_LED_MARKET" and plan == "PLAN_B_COMBINED_CONTEXT":
            return "ENTER", 0.70, reasons + ["COMPACT_PLAN_B_REDUCE"]
        if market_regime == "RISK_OFF_ALT_WEAK" and plan == "PLAN_A_ICT_FAT_TAIL":
            return "ENTER", 0.70, reasons + ["COMPACT_RELATIVE_STRENGTH_PLAN_A"]
        if market_regime == "RISK_OFF_ALT_WEAK":
            return "ENTER", 0.35, reasons + ["COMPACT_RISK_OFF_REDUCE"]
        if market_regime == "MARKET_WEAK_CASH_FLOW" and ("FVG_OB_OVERLAP" in setup or "LIQUIDITY_SWEEP" in setup):
            return "ENTER", 0.35, reasons + ["COMPACT_A_PLUS_ONLY"]
        if market_regime == "MARKET_WEAK_CASH_FLOW":
            return "SKIP", 0.0, reasons + ["COMPACT_OBSERVATION"]
        return "ENTER", 1.0, reasons + ["COMPACT_NORMAL"]

    return "ENTER", 1.0, reasons


def _unit_pnl(trade: dict[str, Any], position_krw: float) -> float:
    entry = float(trade.get("entry_price", 0.0))
    exit_price = float(trade.get("exit_price", 0.0))
    if entry <= 0:
        return 0.0
    return position_krw * ((exit_price / entry) - 1.0) - position_krw * 0.001


def _summary(name: str, data: dict[str, Any], initial_cash: float) -> dict[str, Any]:
    rows = [row for row in data["journal"] if row["defense_action"] == "ENTER" and row["lookahead_check"] == "PASS"]
    pnls = [float(row["pnl_krw"]) for row in rows]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
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
        "trade_count": len(rows),
        "skipped_trade_count": len(data["journal"]) - len(rows),
        "return_mdd_ratio": ret / abs(mdd) if mdd else 0.0,
        "lookahead_fail_count": sum(1 for row in data["journal"] if row["lookahead_check"] != "PASS"),
        "decision": "BASELINE" if name == "CONTROL_EXISTING" else "PENDING",
    }


def _control_from_existing_reports(reports_dir: str | Path, initial_cash: float) -> dict[str, Any]:
    path = Path(reports_dir) / "latest_v66_btcd_scenario_comparison_summary.json"
    if path.exists():
        data = __import__("json").loads(path.read_text(encoding="utf-8-sig"))
        control = next((row for row in data.get("scenarios", []) if row.get("scenario") == "CONTROL_EXISTING"), None)
        if control:
            item = dict(control)
            item["decision"] = "BASELINE"
            return item
    return {"scenario": "CONTROL_EXISTING", "final_equity_krw": initial_cash, "total_return_pct": 0.0, "mdd_pct": 0.0, "profit_factor": 0.0, "trade_count": 0, "return_mdd_ratio": 0.0, "decision": "BASELINE"}


def _data_required_summary(name: str) -> dict[str, Any]:
    return {"scenario": name, "final_equity_krw": None, "total_return_pct": None, "mdd_pct": None, "profit_factor": None, "trade_count": 0, "return_mdd_ratio": None, "decision": "GLOBAL_BTCD_DATA_REQUIRED"}


def _saved_loss_missed_profit(scenario_data: dict[str, Any]) -> list[dict[str, Any]]:
    control = {row["trade_id"]: row for row in scenario_data["CONTROL_EXISTING"]["journal"]}
    rows = []
    for scenario, data in scenario_data.items():
        if scenario == "CONTROL_EXISTING":
            continue
        saved = missed = 0.0
        skipped = [row for row in data["journal"] if row["defense_action"] != "ENTER"]
        for row in skipped:
            pnl = float(control.get(row["trade_id"], {}).get("pnl_krw", 0.0))
            if pnl < 0:
                saved += -pnl
            elif pnl > 0:
                missed += pnl
        rows.append({"scenario": scenario, "saved_loss_krw": saved, "missed_profit_krw": missed, "net_effect_krw": saved - missed, "decision": "KEEP_CANDIDATE" if saved > missed else "REJECT"})
    return rows


def _reject_or_keep(scenarios: list[dict[str, Any]], saved: list[dict[str, Any]], quality: dict[str, Any]) -> list[dict[str, Any]]:
    control = next(row for row in scenarios if row["scenario"] == "CONTROL_EXISTING")
    saved_by = {row["scenario"]: row for row in saved}
    rows = []
    for row in scenarios:
        item = dict(row)
        if item["scenario"] == "CONTROL_EXISTING":
            item["decision"] = "BASELINE"
        elif quality.get("data_quality") != "GOOD":
            item["decision"] = "GLOBAL_BTCD_DATA_REQUIRED"
        elif item["lookahead_fail_count"]:
            item["decision"] = "GLOBAL_BTCD_FILTER_REJECTED"
        elif item["return_mdd_ratio"] > control["return_mdd_ratio"] and saved_by.get(item["scenario"], {}).get("net_effect_krw", 0.0) >= 0:
            item["decision"] = "GLOBAL_BTCD_RELATIVE_STRENGTH_CANDIDATE" if "RELATIVE" in item["scenario"] else "BEAR_REGIME_CANDIDATE"
        else:
            item["decision"] = "GLOBAL_BTCD_FILTER_REJECTED"
        rows.append(item)
    return rows


def _yearly_comparison(scenario_data: dict[str, Any]) -> list[dict[str, Any]]:
    control = {row["period"]: row for row in _period_rows(scenario_data["CONTROL_EXISTING"]["journal"])}
    candidates = [name for name in scenario_data if name != "CONTROL_EXISTING"]
    best_name = candidates[0] if candidates else "CONTROL_EXISTING"
    best_rows = {row["period"]: row for row in _period_rows(scenario_data[best_name]["journal"])}
    return [{"year": year, "control_return_pct": c["return_pct"], "best_global_btcd_scenario": best_name, "best_global_btcd_return_pct": best_rows.get(year, {}).get("return_pct", 0.0), "delta_pct_point": best_rows.get(year, {}).get("return_pct", 0.0) - c["return_pct"], "notes": "Computed from causal rows"} for year, c in control.items()]


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


def _regime_effect(journal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        groups[str(row.get("market_regime", "UNKNOWN"))].append(row)
    return [{"regime": k, "trade_count": len(v), "effect_krw": sum(float(row.get("pnl_krw", 0.0)) for row in v), "decision": "KEEP" if sum(float(row.get("pnl_krw", 0.0)) for row in v) >= 0 else "REJECT"} for k, v in sorted(groups.items())]


def _audit(scenario_data: dict[str, Any]) -> dict[str, Any]:
    total = sum(len(data["journal"]) for data in scenario_data.values())
    fails = sum(1 for data in scenario_data.values() for row in data["journal"] if row["lookahead_check"] != "PASS")
    return {"checked_trades": total, "pass": total - fails, "fail": fails, "excluded_trades": fails, "major_violations": [] if fails == 0 else ["BTCD/BTC feature timestamp after decision"]}


def _empty_audit() -> dict[str, Any]:
    return {"checked_trades": 0, "pass": 0, "fail": 0, "excluded_trades": 0, "major_violations": ["GLOBAL_BTCD_DATA_REQUIRED"]}


def _package(initial_cash: float, quality: dict[str, Any], scenarios: list[dict[str, Any]], saved: list[dict[str, Any]], yearly: list[dict[str, Any]], regime: list[dict[str, Any]], audit: dict[str, Any], full_possible: bool) -> dict[str, Any]:
    return {
        "schema_version": "v67_global_btcd_scenario_lab_v1",
        "initial_cash_krw": initial_cash,
        "global_btcd_history_quality": quality,
        "full_period_validation_possible": full_possible,
        "reason": "Global BTCD historical data available." if full_possible else quality.get("notes", "Global BTCD historical data required."),
        "scenarios": scenarios,
        "saved_loss_missed_profit": saved,
        "yearly_comparison": yearly,
        "regime_effect": regime,
        "audit": audit,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
