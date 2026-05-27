from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from analysis.v66_btcd_scenario_analyzer import load_true_walk_forward_journal
from btcd.btc_trend_feature_builder import BTCTrendFeatureStore
from btcd.btcdom_index_alignment import btcdom_lookahead_pass
from btcd.btcdom_index_feature_builder import BTCDOMIndexFeatureStore
from btcd.btcdom_index_regime_classifier import classify_btcdom_market_state
from btcd.btcdom_index_data_quality import load_btcdom_index_quality
from risk.risk_position_sizer import size_position


SCENARIOS = [
    "CONTROL_EXISTING",
    "BTCDOM_INDEX_RELATIVE_STRENGTH_FILTER",
    "BTCDOM_INDEX_ALT_PERMISSION_FILTER",
    "BTCDOM_INDEX_BEAR_DEFENSE_FILTER",
    "BTCDOM_INDEX_COMPACT_ROUTER",
]


def analyze_v672_btcdom_index_scenarios(
    initial_cash_krw: float = 500000.0,
    reports_dir: str | Path = "docs/reports",
    archive_dir: str | Path = "replay_store/historical_archive",
    processed_dir: str | Path = "data/processed",
) -> dict[str, Any]:
    source_journal = sorted(load_true_walk_forward_journal(reports_dir), key=lambda row: str(row.get("entry_time", "")))
    quality = load_btcdom_index_quality(reports_dir)
    if quality.get("data_quality") != "GOOD":
        control = _control_from_existing_reports(reports_dir, initial_cash_krw)
        scenarios = [control] + [_data_required_summary(s) for s in SCENARIOS if s != "CONTROL_EXISTING"]
        return _package(initial_cash_krw, quality, scenarios, [], [], [], _empty_audit(), False)
    start = str(quality.get("common_coverage_start"))
    end = str(quality.get("common_coverage_end"))
    journal = [row for row in source_journal if start <= str(row.get("entry_time", "")) <= end]
    store = BTCDOMIndexFeatureStore(processed_dir)
    btc_store = BTCTrendFeatureStore(archive_dir)
    scenario_data = {scenario: _simulate(scenario, journal, initial_cash_krw, store, btc_store) for scenario in SCENARIOS}
    scenarios = [_summary(name, data, initial_cash_krw) for name, data in scenario_data.items()]
    saved = _saved_loss_missed_profit(scenario_data)
    scenarios = _decide(scenarios, saved)
    yearly = _yearly_comparison(scenario_data)
    regime = _regime_effect(scenario_data["CONTROL_EXISTING"]["journal"])
    audit = _audit(scenario_data)
    return _package(initial_cash_krw, quality, scenarios, saved, yearly, regime, audit, True)


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
        state = classify_btcdom_market_state(feature, btc)
        action, multiplier, reasons = _action(scenario, trade, state)
        sizing = size_position(equity, float(trade.get("entry_price", 0.0)), float(trade.get("stop_price", 0.0)))
        if not sizing.get("sizing_valid"):
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
                "decision_time": decision_time,
                "entry_time": entry_time,
                "feature_cutoff_time": str(trade.get("feature_cutoff_time") or decision_time),
                "btcdom_feature_time_1h": feature.get("btcdom_feature_time_1h"),
                "btcdom_feature_time_4h": feature.get("btcdom_feature_time_4h"),
                "btcdom_feature_time_1d": feature.get("btcdom_feature_time_1d"),
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
                "btcdom_regime": state.get("btcdom_regime"),
                "market_state": state.get("market_state"),
                "used_future_data": not lookahead_pass,
                "lookahead_check": "PASS" if lookahead_pass else "FAIL",
                "real_order_enabled": False,
                "live_order_allowed": False,
                "auto_apply_allowed": False,
            }
        )
    return {"journal": rows}


def _action(scenario: str, trade: dict[str, Any], state: dict[str, Any]) -> tuple[str, float, list[str]]:
    if scenario == "CONTROL_EXISTING":
        return "ENTER", 1.0, ["BTCDOM_INDEX_NOT_USED_CONTROL"]
    market_state = str(state.get("market_state"))
    plan = str(trade.get("plan"))
    setup = str(trade.get("setup_type"))
    strong_setup = plan == "PLAN_A_ICT_FAT_TAIL" or "FVG_OB_OVERLAP" in setup or "LIQUIDITY_SWEEP" in setup
    reasons = [market_state, str(state.get("btcdom_regime"))]
    if scenario == "BTCDOM_INDEX_RELATIVE_STRENGTH_FILTER":
        if market_state == "RISK_OFF_ALT_WEAK" and strong_setup:
            return "ENTER", 0.70, reasons + ["RELATIVE_STRENGTH_ONLY"]
        if market_state == "RISK_OFF_ALT_WEAK":
            return "SKIP", 0.0, reasons + ["WEAK_ALT_BLOCK"]
        if market_state == "MARKET_WEAK_CASH_FLOW" and strong_setup:
            return "ENTER", 0.35, reasons + ["A_PLUS_WEAK_MARKET_SMALL_SIZE"]
        if market_state == "MARKET_WEAK_CASH_FLOW":
            return "SKIP", 0.0, reasons + ["OBSERVATION_ONLY"]
        return "ENTER", 1.0, reasons + ["PASS"]
    if scenario == "BTCDOM_INDEX_ALT_PERMISSION_FILTER":
        if market_state == "BTC_LED_MARKET":
            return "ENTER", 0.70, reasons + ["BTC_LED_REDUCE"]
        if market_state in {"RISK_OFF_ALT_WEAK", "MARKET_WEAK_CASH_FLOW"}:
            return "ENTER", 0.35, reasons + ["ALT_PERMISSION_REDUCE"]
        return "ENTER", 1.0, reasons + ["ALLOW"]
    if scenario == "BTCDOM_INDEX_BEAR_DEFENSE_FILTER":
        if market_state in {"RISK_OFF_ALT_WEAK", "MARKET_WEAK_CASH_FLOW"} and not strong_setup:
            return "ENTER", 0.35, reasons + ["BEAR_DEFENSE_REDUCE_NON_A_PLUS"]
        if market_state in {"RISK_OFF_ALT_WEAK", "MARKET_WEAK_CASH_FLOW"}:
            return "ENTER", 0.50, reasons + ["BEAR_DEFENSE_A_PLUS_LIMIT"]
        return "ENTER", 1.0, reasons + ["PASS"]
    if scenario == "BTCDOM_INDEX_COMPACT_ROUTER":
        if market_state == "ALT_FRIENDLY":
            return "ENTER", 1.0, reasons + ["ALT_FRIENDLY"]
        if market_state == "BTC_LED_MARKET" and plan == "PLAN_B_COMBINED_CONTEXT":
            return "ENTER", 0.70, reasons + ["PLAN_B_REDUCE"]
        if market_state == "RISK_OFF_ALT_WEAK" and strong_setup:
            return "ENTER", 0.70, reasons + ["STRONG_ONLY"]
        if market_state == "RISK_OFF_ALT_WEAK":
            return "ENTER", 0.35, reasons + ["RISK_OFF_REDUCE"]
        if market_state == "MARKET_WEAK_CASH_FLOW" and strong_setup:
            return "ENTER", 0.35, reasons + ["A_PLUS_ONLY"]
        if market_state == "MARKET_WEAK_CASH_FLOW":
            return "SKIP", 0.0, reasons + ["OBSERVATION"]
        return "ENTER", 1.0, reasons + ["NORMAL"]
    return "ENTER", 1.0, reasons


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
    path = Path(reports_dir) / "latest_true_walk_forward_summary.json"
    if path.exists():
        import json

        data = json.loads(path.read_text(encoding="utf-8-sig"))
        capital = data.get("capital", {})
        if capital:
            return {
                "scenario": "CONTROL_EXISTING",
                "final_equity_krw": capital.get("final_equity_krw", initial_cash),
                "total_return_pct": capital.get("total_return_pct", 0.0),
                "mdd_pct": capital.get("max_drawdown_pct", 0.0),
                "profit_factor": capital.get("profit_factor", 0.0),
                "trade_count": capital.get("trade_count", 0),
                "return_mdd_ratio": 0.0,
                "decision": "BASELINE",
            }
    return {"scenario": "CONTROL_EXISTING", "final_equity_krw": initial_cash, "total_return_pct": 0.0, "mdd_pct": 0.0, "profit_factor": 0.0, "trade_count": 0, "return_mdd_ratio": 0.0, "decision": "BASELINE"}


def _data_required_summary(name: str) -> dict[str, Any]:
    return {"scenario": name, "final_equity_krw": None, "total_return_pct": None, "mdd_pct": None, "profit_factor": None, "trade_count": 0, "return_mdd_ratio": None, "decision": "BTCDOM_INDEX_DATA_REQUIRED"}


def _saved_loss_missed_profit(scenario_data: dict[str, Any]) -> list[dict[str, Any]]:
    control = {row["trade_id"]: row for row in scenario_data["CONTROL_EXISTING"]["journal"]}
    rows = []
    for scenario, data in scenario_data.items():
        if scenario == "CONTROL_EXISTING":
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
    control = next(row for row in scenarios if row["scenario"] == "CONTROL_EXISTING")
    saved_by = {row["scenario"]: row for row in saved}
    out = []
    for row in scenarios:
        item = dict(row)
        if item["scenario"] == "CONTROL_EXISTING":
            item["decision"] = "BASELINE"
        elif item["lookahead_fail_count"]:
            item["decision"] = "BTCDOM_INDEX_FILTER_REJECTED"
        elif item["return_mdd_ratio"] > control["return_mdd_ratio"] and saved_by.get(item["scenario"], {}).get("net_effect_krw", 0.0) >= 0:
            item["decision"] = "BTCDOM_RELATIVE_STRENGTH_CANDIDATE" if "RELATIVE" in item["scenario"] else "BTCDOM_INDEX_FILTER_VALIDATED"
        else:
            item["decision"] = "BTCDOM_INDEX_FILTER_REJECTED"
        out.append(item)
    return out


def _yearly_comparison(scenario_data: dict[str, Any]) -> list[dict[str, Any]]:
    control = {row["period"]: row for row in _period_rows(scenario_data["CONTROL_EXISTING"]["journal"])}
    candidates = [name for name in scenario_data if name != "CONTROL_EXISTING"]
    best = max(candidates, key=lambda name: _final_equity(scenario_data[name])) if candidates else "CONTROL_EXISTING"
    best_rows = {row["period"]: row for row in _period_rows(scenario_data[best]["journal"])}
    return [{"year": year, "control_return_pct": c["return_pct"], "best_btcdom_scenario": best, "best_btcdom_return_pct": best_rows.get(year, {}).get("return_pct", 0.0), "delta_pct_point": best_rows.get(year, {}).get("return_pct", 0.0) - c["return_pct"], "notes": "BTCDOM coverage period only"} for year, c in control.items()]


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


def _final_equity(data: dict[str, Any]) -> float:
    return float(data["journal"][-1]["equity_after"]) if data["journal"] else 0.0


def _regime_effect(journal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        groups[str(row.get("market_state", "UNKNOWN"))].append(row)
    return [{"regime": k, "effect_krw": sum(float(row.get("pnl_krw", 0.0)) for row in v), "trade_count": len(v), "decision": "KEEP" if sum(float(row.get("pnl_krw", 0.0)) for row in v) >= 0 else "REJECT"} for k, v in sorted(groups.items())]


def _audit(scenario_data: dict[str, Any]) -> dict[str, Any]:
    total = sum(len(data["journal"]) for data in scenario_data.values())
    fails = sum(1 for data in scenario_data.values() for row in data["journal"] if row["lookahead_check"] != "PASS")
    return {"checked_trades": total, "pass": total - fails, "fail": fails, "excluded_trades": fails, "major_violations": [] if fails == 0 else ["BTCDOM feature timestamp after decision"]}


def _empty_audit() -> dict[str, Any]:
    return {"checked_trades": 0, "pass": 0, "fail": 0, "excluded_trades": 0, "major_violations": ["BTCDOM_INDEX_DATA_REQUIRED"]}


def _package(initial_cash: float, quality: dict[str, Any], scenarios: list[dict[str, Any]], saved: list[dict[str, Any]], yearly: list[dict[str, Any]], regime: list[dict[str, Any]], audit: dict[str, Any], possible: bool) -> dict[str, Any]:
    return {
        "schema_version": "v672_btcdom_index_scenario_lab_v1",
        "initial_cash_krw": initial_cash,
        "btcdom_index_quality": quality,
        "coverage_period_validation_possible": possible,
        "reason": "BTCDOM Index data available." if possible else "BTCDOM Index data required.",
        "scenarios": scenarios,
        "saved_loss_missed_profit": saved,
        "yearly_comparison": yearly,
        "regime_effect": regime,
        "audit": audit,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
