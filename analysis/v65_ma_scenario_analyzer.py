from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ma_strategy.daddy_ma_regime_detector import detect_daddy_ma_states
from ma_strategy.ma_no_trade_gate import should_no_trade
from ma_strategy.ma_policy_router import route_policy
from ma_strategy.ma_quality_scorer import score_ma_quality
from ma_strategy.ma_schema import MAFeature, MAValue
from ma_strategy.testa_ma_alignment_detector import detect_testa_states
from portfolio.causal_equity_defense_runner import _decide_multiplier, _drawdown
from portfolio.dynamic_risk_scaler import DynamicRiskScaler
from portfolio.profit_lock_engine import ProfitLockEngine
from portfolio.protected_floor_manager import ProtectedFloorManager
from risk.risk_position_sizer import size_position


SCENARIOS = [
    "CONTROL_CURRENT_ROUTER",
    "MA_FILTER_ONLY",
    "MA_QUALITY_SCORE",
    "MA_POLICY_ROUTER",
    "MA_DEFENSIVE_REPAIR",
    "MA_SQUEEZE_RESEARCH",
]


@dataclass
class ScenarioDecision:
    action: str
    multiplier: float
    policy: str
    reasons: list[str]
    decision: str


class MAFeatureStore:
    def __init__(self, archive_dir: str | Path = "replay_store/historical_archive") -> None:
        self.archive_dir = Path(archive_dir)
        self._cache: dict[tuple[str, str], pd.DataFrame] = {}

    def feature_for(self, market: str, decision_time: str) -> MAFeature:
        dt = pd.Timestamp(decision_time)
        rows = {
            timeframe: self._latest_row(market, timeframe, dt)
            for timeframe in ("1d", "4h", "1h")
        }
        primary = rows.get("1h") or rows.get("4h") or rows.get("1d") or {}
        states: list[str] = []
        reasons: list[str] = []
        values: dict[str, MAValue] = {}
        for timeframe, row in rows.items():
            if not row:
                continue
            row_states = detect_daddy_ma_states(row) + detect_testa_states(row)
            states.extend(row_states)
            for period in (5, 20, 25, 75, 200):
                key = f"{timeframe}_sma{period}"
                values[key] = MAValue(
                    timeframe=timeframe,
                    ma_type="SMA",
                    period=period,
                    value=_optional_float(row.get(f"sma{period}")),
                    slope_pct=_optional_float(row.get(f"sma{period}_slope_pct")),
                    meaning=f"{period} bars on {timeframe} timeframe, not 200 days unless timeframe is 1d",
                )
            if row_states:
                reasons.append(f"{timeframe}: {', '.join(row_states)}")
        unique_states = sorted(set(states))
        score, score_reasons = score_ma_quality(unique_states)
        feature_time = str(primary.get("time", decision_time))
        lookahead_ok = pd.Timestamp(feature_time) <= dt
        return MAFeature(
            market=market,
            feature_time=feature_time,
            ma_timeframe=str(primary.get("timeframe", "UNKNOWN")),
            close=float(primary.get("close", 0.0) or 0.0),
            values=values,
            states=unique_states,
            score=score,
            reasons=reasons + score_reasons,
            used_future_data=not lookahead_ok,
            lookahead_check="PASS" if lookahead_ok else "FAIL",
        )

    def _latest_row(self, market: str, timeframe: str, decision_time: pd.Timestamp) -> dict[str, Any]:
        frame = self._load(market, timeframe)
        if frame.empty:
            return {}
        eligible = frame[frame["time"] <= decision_time]
        if eligible.empty:
            return {}
        return eligible.iloc[-1].to_dict()

    def _load(self, market: str, timeframe: str) -> pd.DataFrame:
        key = (market, timeframe)
        if key in self._cache:
            return self._cache[key]
        path = self.archive_dir / timeframe / f"{market}.parquet"
        if not path.exists():
            self._cache[key] = pd.DataFrame()
            return self._cache[key]
        frame = pd.read_parquet(path).sort_values("time").reset_index(drop=True)
        for period in (5, 20, 25, 75, 200):
            frame[f"sma{period}"] = frame["close"].rolling(period).mean()
            frame[f"sma{period}_slope_pct"] = frame[f"sma{period}"].pct_change(5, fill_method=None) * 100.0
        frame["volume_sma20"] = frame["volume"].rolling(20).mean()
        self._cache[key] = frame
        return frame


def build_ma_feature_summary(
    journal: list[dict[str, Any]],
    archive_dir: str | Path = "replay_store/historical_archive",
) -> dict[str, Any]:
    store = MAFeatureStore(archive_dir)
    state_counts: Counter[str] = Counter()
    market_counts: Counter[str] = Counter()
    features: list[dict[str, Any]] = []
    lookahead_fail = 0
    for trade in sorted(journal, key=lambda row: str(row.get("entry_time", ""))):
        decision_time = str(trade.get("feature_cutoff_time") or trade.get("entry_time"))
        feature = store.feature_for(str(trade.get("market")), decision_time)
        for state in feature.states:
            state_counts[state] += 1
        market_counts[str(trade.get("market"))] += 1
        if feature.lookahead_check != "PASS":
            lookahead_fail += 1
        features.append({"trade_id": trade.get("trade_id"), **feature.as_dict()})
    return {
        "schema_version": "v65_ma_features_v1",
        "feature_count": len(features),
        "state_counts": dict(sorted(state_counts.items())),
        "market_counts": dict(market_counts.most_common(20)),
        "lookahead_fail_count": lookahead_fail,
        "features": features,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def analyze_v65_ma_scenarios(
    journal: list[dict[str, Any]],
    initial_cash_krw: float = 500000.0,
    archive_dir: str | Path = "replay_store/historical_archive",
) -> dict[str, Any]:
    ordered = sorted(journal, key=lambda row: str(row.get("entry_time", "")))
    store = MAFeatureStore(archive_dir)
    scenario_data = {scenario: _simulate_scenario(scenario, ordered, store, initial_cash_krw) for scenario in SCENARIOS}
    control = _scenario_summary("CONTROL_CURRENT_ROUTER", scenario_data["CONTROL_CURRENT_ROUTER"], initial_cash_krw)
    scenarios = [_scenario_summary(name, data, initial_cash_krw) for name, data in scenario_data.items()]
    return {
        "schema_version": "v65_ma_scenario_lab_v1",
        "initial_cash_krw": initial_cash_krw,
        "scenarios": scenarios,
        "ma_feature_counts": _feature_counts_from_data(scenario_data["CONTROL_CURRENT_ROUTER"]),
        "yearly_comparison": _yearly_comparison(control, scenario_data, initial_cash_krw),
        "weak_year_repair": _weak_year_repair(scenario_data, initial_cash_krw),
        "plan_impact": _group_impact(scenario_data, "plan"),
        "setup_impact": _group_impact(scenario_data, "setup_type"),
        "ma_condition_effect": _ma_condition_effect(scenario_data),
        "policy_router": _router_summary(scenario_data["MA_POLICY_ROUTER"]),
        "risk_summary": _risk_summary(scenario_data),
        "audit": _audit(scenario_data),
        "equity_curve": {name: _sample(data["equity_curve"]) for name, data in scenario_data.items()},
        "drawdown_curve": {name: _sample(data["drawdown_curve"]) for name, data in scenario_data.items()},
        "recommendation": _recommendation(scenarios),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def _simulate_scenario(
    scenario: str,
    source_journal: list[dict[str, Any]],
    store: MAFeatureStore,
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

    for idx, trade in enumerate(source_journal):
        decision_time = str(trade.get("feature_cutoff_time") or trade.get("signal_time") or trade.get("entry_time"))
        feature = store.feature_for(str(trade.get("market")), decision_time)
        drawdown_before = _drawdown(equity, peak)
        base_policy = _base_policy_for_scenario(scenario, trade, feature)
        base_decision = _decide_multiplier(base_policy, trade, equity, drawdown_before, scaler, profit_lock)
        scenario_decision = _scenario_decision(scenario, trade, feature, base_decision)
        action = scenario_decision.action
        multiplier = scenario_decision.multiplier
        sizing = size_position(equity, float(trade.get("entry_price", 0.0)), float(trade.get("stop_price", 0.0)))
        reasons = list(base_decision.get("defense_reasons") or ["NO_DEFENSE"]) + scenario_decision.reasons
        if not sizing.get("sizing_valid"):
            action = "SKIP"
            multiplier = 0.0
            reasons.append(str(sizing.get("reason") or "INVALID_SIZING"))

        pnl = 0.0
        position_krw = 0.0
        if action == "ENTER" and multiplier > 0:
            base_position = min(float(sizing["position_krw"]), equity)
            unit_full = _unit_pnl(trade, base_position)
            floor_multiplier, floor_capped = floor_manager.cap_multiplier(equity, unit_full, multiplier)
            if floor_capped:
                multiplier = floor_multiplier
                reasons.append("PROTECTED_FLOOR_CAP")
            position_krw = base_position * multiplier
            pnl = _unit_pnl(trade, position_krw)
            scaler.record(pnl, str(trade.get("exit_time")))

        equity_before = equity
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        drawdown_after = _drawdown(equity, peak)
        entry_time = str(trade.get("entry_time"))
        feature_cutoff_time = str(trade.get("feature_cutoff_time") or decision_time)
        lookahead_pass = feature_cutoff_time <= decision_time <= entry_time and feature.lookahead_check == "PASS"
        row = {
            "trade_id": trade.get("trade_id"),
            "date": entry_time[:10],
            "entry_time": entry_time,
            "exit_time": trade.get("exit_time"),
            "market": trade.get("market"),
            "plan": trade.get("plan"),
            "strategy": trade.get("strategy"),
            "setup_type": trade.get("setup_type"),
            "scenario": scenario,
            "entry_price": float(trade.get("entry_price", 0.0)),
            "exit_price": float(trade.get("exit_price", 0.0)),
            "stop_price": float(trade.get("stop_price", 0.0)),
            "position_krw": position_krw,
            "risk_amount_krw": float(sizing.get("risk_amount_krw", 0.0)) * multiplier,
            "pnl_krw": pnl,
            "return_pct": pnl / equity_before * 100.0 if equity_before else 0.0,
            "equity_before": equity_before,
            "equity_after": equity,
            "drawdown_pct": drawdown_after,
            "defense_state_before_trade": base_decision["defense_state_before_trade"],
            "defense_action": action,
            "defense_reasons": reasons,
            "risk_multiplier_after_defense": multiplier if action == "ENTER" else 0.0,
            "ma_states": feature.states,
            "ma_score": feature.score,
            "ma_feature_time": feature.feature_time,
            "ma_timeframe": feature.ma_timeframe,
            "ma_decision": scenario_decision.decision,
            "feature_cutoff_time": feature_cutoff_time,
            "decision_time": decision_time,
            "used_future_data": not lookahead_pass,
            "lookahead_check": "PASS" if lookahead_pass else "FAIL",
            "real_order_enabled": False,
            "live_order_allowed": False,
            "auto_apply_allowed": False,
        }
        rows.append(row)
        equity_curve.append({"sequence": idx, "time": trade.get("exit_time"), "equity": equity})
        drawdown_curve.append({"sequence": idx, "time": trade.get("exit_time"), "drawdown_pct": drawdown_after})

    return {"journal": rows, "equity_curve": equity_curve, "drawdown_curve": drawdown_curve}


def _base_policy_for_scenario(scenario: str, trade: dict[str, Any], feature: MAFeature) -> str:
    if scenario == "MA_POLICY_ROUTER":
        if str(trade.get("plan")) == "PLAN_A_ICT_FAT_TAIL":
            return "ROLLING_EDGE_THROTTLE"
        return "BALANCED_GROWTH"
    if scenario == "CONTROL_CURRENT_ROUTER":
        return "BALANCED_GROWTH"
    return "BALANCED_GROWTH"


def _scenario_decision(
    scenario: str,
    trade: dict[str, Any],
    feature: MAFeature,
    base_decision: dict[str, Any],
) -> ScenarioDecision:
    states = feature.states
    base_multiplier = float(base_decision["risk_multiplier_after_defense"])
    defense_state = str(base_decision["defense_state_before_trade"])
    if base_decision.get("defense_action") == "SKIP" or base_multiplier <= 0:
        return ScenarioDecision("SKIP", 0.0, "BASE_SKIP", ["BASE_POLICY_SKIP"], "BASE_SKIP")

    if scenario == "CONTROL_CURRENT_ROUTER":
        return ScenarioDecision("ENTER", base_multiplier, "BALANCED_GROWTH", ["CONTROL_NO_MA"], "ENTER")
    if scenario == "MA_FILTER_ONLY":
        if should_no_trade(states):
            return ScenarioDecision("SKIP", 0.0, "MA_FILTER_ONLY", ["MA_BEAR_OR_LOST_75"], "NO_TRADE")
        if "MA_CHOP" in states or "TESTA_CHOP" in states or "MA_OVEREXTENDED" in states:
            return ScenarioDecision("ENTER", base_multiplier * 0.35, "MA_FILTER_ONLY", ["MA_CHOP_OR_OVEREXTENDED_REDUCE"], "REDUCE")
        return ScenarioDecision("ENTER", base_multiplier, "MA_FILTER_ONLY", ["MA_FILTER_PASS"], "ENTER")
    if scenario == "MA_QUALITY_SCORE":
        if "TESTA_LOST_75" in states:
            return ScenarioDecision("SKIP", 0.0, "MA_QUALITY_SCORE", ["TESTA_LOST_75"], "NO_TRADE")
        if feature.score >= 75:
            return ScenarioDecision("ENTER", base_multiplier, "MA_QUALITY_SCORE", ["MA_QUALITY_A"], "ENTER")
        if feature.score >= 55:
            return ScenarioDecision("ENTER", base_multiplier * 0.70, "MA_QUALITY_SCORE", ["MA_QUALITY_B"], "REDUCE")
        if feature.score >= 40:
            return ScenarioDecision("ENTER", base_multiplier * 0.35, "MA_QUALITY_SCORE", ["MA_QUALITY_C"], "REDUCE")
        return ScenarioDecision("SKIP", 0.0, "MA_QUALITY_SCORE", ["MA_QUALITY_D"], "NO_TRADE")
    if scenario == "MA_POLICY_ROUTER":
        routed = route_policy(trade, states, feature.score, defense_state)
        if routed["policy"] in {"ROLLING_EDGE_THROTTLE", "BALANCED_GROWTH"}:
            policy_multiplier = base_multiplier if routed["policy"] == "BALANCED_GROWTH" else min(base_multiplier, 1.0)
            return ScenarioDecision("ENTER", policy_multiplier * float(routed["multiplier_scale"]), routed["policy"], list(routed["reason"]), "ENTER")
        if float(routed["multiplier_scale"]) > 0:
            return ScenarioDecision("ENTER", base_multiplier * float(routed["multiplier_scale"]), routed["policy"], list(routed["reason"]), "REDUCE")
        return ScenarioDecision("SKIP", 0.0, routed["policy"], list(routed["reason"]), "NO_TRADE")
    if scenario == "MA_DEFENSIVE_REPAIR":
        if defense_state == "CAUTION" and ("MA_CHOP" in states or "TESTA_CHOP" in states):
            return ScenarioDecision("SKIP", 0.0, "MA_DEFENSIVE_REPAIR", ["CAUTION_MA_CHOP_NO_TRADE"], "NO_TRADE")
        if defense_state == "DEFENSIVE":
            if "MA_BULL" in states and "TESTA_BULL_ALIGNMENT" in states and feature.score >= 80:
                return ScenarioDecision("ENTER", min(base_multiplier, 0.35), "MA_DEFENSIVE_REPAIR", ["DEFENSIVE_A_PLUS_MA_ONLY"], "REDUCE")
            return ScenarioDecision("SKIP", 0.0, "MA_DEFENSIVE_REPAIR", ["DEFENSIVE_MA_REPAIR_SKIP"], "NO_TRADE")
        if should_no_trade(states):
            return ScenarioDecision("SKIP", 0.0, "MA_DEFENSIVE_REPAIR", ["MA_BEAR_OR_LOST_75"], "NO_TRADE")
        return ScenarioDecision("ENTER", base_multiplier, "MA_DEFENSIVE_REPAIR", ["MA_DEFENSIVE_PASS"], "ENTER")
    if scenario == "MA_SQUEEZE_RESEARCH":
        if should_no_trade(states):
            return ScenarioDecision("SKIP", 0.0, "MA_SQUEEZE_RESEARCH", ["MA_BEAR_OR_LOST_75"], "NO_TRADE")
        if "MA_SQUEEZE_BREAKOUT" in states and str(trade.get("plan")) in {"PLAN_A_ICT_FAT_TAIL", "PLAN_B_COMBINED_CONTEXT"}:
            return ScenarioDecision("ENTER", min(base_multiplier * 1.25, 1.5), "MA_SQUEEZE_RESEARCH", ["SQUEEZE_RESEARCH_BOOST"], "BOOST")
        if "MA_CHOP" in states:
            return ScenarioDecision("ENTER", base_multiplier * 0.35, "MA_SQUEEZE_RESEARCH", ["SQUEEZE_CHOP_REDUCE"], "REDUCE")
        return ScenarioDecision("ENTER", base_multiplier, "MA_SQUEEZE_RESEARCH", ["SQUEEZE_RESEARCH_PASS"], "ENTER")
    return ScenarioDecision("ENTER", base_multiplier, scenario, ["DEFAULT"], "ENTER")


def _unit_pnl(trade: dict[str, Any], position_krw: float) -> float:
    entry = float(trade.get("entry_price", 0.0))
    exit_price = float(trade.get("exit_price", 0.0))
    if entry <= 0:
        return 0.0
    return position_krw * ((exit_price / entry) - 1.0) - position_krw * 0.001


def _scenario_summary(name: str, data: dict[str, Any], initial_cash: float) -> dict[str, Any]:
    entered = [row for row in data["journal"] if row["defense_action"] == "ENTER" and row["lookahead_check"] == "PASS"]
    skipped = [row for row in data["journal"] if row["defense_action"] != "ENTER"]
    pnls = [float(row["pnl_krw"]) for row in entered]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    final = float(data["journal"][-1]["equity_after"]) if data["journal"] else initial_cash
    mdd = min((float(row["drawdown_pct"]) for row in data["journal"]), default=0.0)
    ret = (final / initial_cash - 1.0) * 100.0 if initial_cash else 0.0
    gross_loss = abs(sum(losses))
    return {
        "scenario": name,
        "final_equity_krw": final,
        "total_return_pct": ret,
        "mdd_pct": mdd,
        "profit_factor": sum(wins) / gross_loss if gross_loss else 99.0 if wins else 0.0,
        "expectancy_pct": ((sum(pnls) / len(pnls)) / initial_cash * 100.0) if pnls else 0.0,
        "trade_count": len(entered),
        "skipped_trade_count": len(skipped),
        "win_rate_pct": len(wins) / len(pnls) * 100.0 if pnls else 0.0,
        "return_mdd_ratio": ret / abs(mdd) if mdd else 0.0,
        "average_position_krw": _avg([float(row["position_krw"]) for row in entered]),
        "lookahead_fail_count": sum(1 for row in data["journal"] if row["lookahead_check"] != "PASS"),
        "decision": _scenario_decision_label(name, ret, mdd),
    }


def _scenario_decision_label(name: str, ret: float, mdd: float) -> str:
    if name == "MA_SQUEEZE_RESEARCH":
        return "RESEARCH_ONLY" if mdd > -30 else "RETURN_AMPLIFICATION_CANDIDATE"
    if ret > 180 and mdd > -20:
        return "POLICY_ROUTER_CANDIDATE"
    if ret > 120:
        return "MA_FILTER_VALIDATED"
    return "MA_FILTER_REJECTED"


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
            "skipped": len(items) - len(entered),
            "win_rate_pct": len(wins) / len(pnls) * 100.0 if pnls else 0.0,
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


def _yearly_comparison(control_summary: dict[str, Any], scenario_data: dict[str, Any], initial_cash: float) -> list[dict[str, Any]]:
    control_rows = {row["period"]: row for row in _period_rows(scenario_data["CONTROL_CURRENT_ROUTER"]["journal"], "year")}
    result = []
    for year, control in control_rows.items():
        row = {"year": year, "control_return_pct": control["return_pct"], "control_trades": control["trades"]}
        for scenario, data in scenario_data.items():
            yearly = {item["period"]: item for item in _period_rows(data["journal"], "year")}
            item = yearly.get(year, {})
            row[f"{scenario}_return_pct"] = item.get("return_pct", 0.0)
            row[f"{scenario}_trade_count"] = item.get("trades", 0)
            row[f"{scenario}_delta_pct_point"] = item.get("return_pct", 0.0) - control["return_pct"]
        result.append(row)
    return result


def _weak_year_repair(scenario_data: dict[str, Any], initial_cash: float) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for scenario, data in scenario_data.items():
        yearly = {row["period"]: row for row in _period_rows(data["journal"], "year")}
        output[scenario] = {
            "2025_return_pct": yearly.get("2025", {}).get("return_pct", 0.0),
            "2026_return_pct": yearly.get("2026", {}).get("return_pct", 0.0),
            "2025_trades": yearly.get("2025", {}).get("trades", 0),
            "2026_trades": yearly.get("2026", {}).get("trades", 0),
            "defensive_state_pnl": _state_pnl(data["journal"], "DEFENSIVE"),
            "caution_state_pnl": _state_pnl(data["journal"], "CAUTION"),
        }
    return output


def _state_pnl(journal: list[dict[str, Any]], state: str) -> float:
    return sum(float(row["pnl_krw"]) for row in journal if row.get("defense_state_before_trade") == state)


def _group_impact(scenario_data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    control = _group_pnl(scenario_data["CONTROL_CURRENT_ROUTER"]["journal"], key)
    rows = []
    for scenario, data in scenario_data.items():
        current = _group_pnl(data["journal"], key)
        for name, pnl in current.items():
            rows.append({
                "scenario": scenario,
                key: name,
                "pnl_krw": pnl,
                "control_pnl_krw": control.get(name, 0.0),
                "delta_krw": pnl - control.get(name, 0.0),
                "trade_count": sum(1 for row in data["journal"] if row.get(key) == name and row["defense_action"] == "ENTER"),
            })
    return rows


def _group_pnl(journal: list[dict[str, Any]], key: str) -> dict[str, float]:
    groups: defaultdict[str, float] = defaultdict(float)
    for row in journal:
        if row["defense_action"] == "ENTER":
            groups[str(row.get(key))] += float(row["pnl_krw"])
    return dict(groups)


def _feature_counts_from_data(data: dict[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in data["journal"]:
        for state in row.get("ma_states", []):
            counts[state] += 1
    return dict(sorted(counts.items()))


def _ma_condition_effect(scenario_data: dict[str, Any]) -> list[dict[str, Any]]:
    conditions = ["MA_CHOP", "MA_SQUEEZE_BREAKOUT", "TESTA_BULL_ALIGNMENT", "TESTA_LOST_75", "MA_OVEREXTENDED"]
    control = scenario_data["CONTROL_CURRENT_ROUTER"]["journal"]
    rows = []
    for condition in conditions:
        affected = [row for row in control if condition in row.get("ma_states", [])]
        control_pnl = sum(float(row["pnl_krw"]) for row in affected)
        rows.append({
            "ma_condition": condition,
            "control_trade_count": len(affected),
            "control_pnl_krw": control_pnl,
            "effect": _condition_effect_text(condition, control_pnl, len(affected)),
            "decision": _condition_decision(condition, control_pnl),
        })
    return rows


def _condition_effect_text(condition: str, pnl: float, count: int) -> str:
    if count == 0:
        return "표본 없음"
    return f"{count}건, 기준 손익 {pnl:,.0f}원"


def _condition_decision(condition: str, pnl: float) -> str:
    if condition == "MA_SQUEEZE_BREAKOUT" and pnl > 0:
        return "KEEP_RESEARCH"
    if condition == "TESTA_BULL_ALIGNMENT" and pnl > 0:
        return "KEEP_AS_QUALITY_BOOST"
    if condition in {"MA_CHOP", "TESTA_LOST_75", "MA_OVEREXTENDED"} and pnl > 0:
        return "REJECT_AS_HARD_FILTER"
    if pnl < 0:
        return "KEEP_AS_FILTER"
    return "OBSERVE"


def _router_summary(data: dict[str, Any]) -> dict[str, Any]:
    decisions = Counter(str(row.get("ma_decision")) for row in data["journal"])
    reasons = Counter(reason for row in data["journal"] for reason in row.get("defense_reasons", []) if reason.startswith("MA") or reason.startswith("PLAN") or reason.startswith("DEFENSIVE"))
    return {"decisions": dict(decisions), "top_reasons": reasons.most_common(12)}


def _risk_summary(scenario_data: dict[str, Any]) -> dict[str, Any]:
    return {
        name: {
            "max_losing_streak": _max_losing_streak(data["journal"]),
            "largest_loss_krw": min((float(row["pnl_krw"]) for row in data["journal"]), default=0.0),
            "largest_win_krw": max((float(row["pnl_krw"]) for row in data["journal"]), default=0.0),
        }
        for name, data in scenario_data.items()
    }


def _max_losing_streak(journal: list[dict[str, Any]]) -> int:
    streak = 0
    longest = 0
    for row in journal:
        if row["defense_action"] == "ENTER" and float(row["pnl_krw"]) < 0:
            streak += 1
            longest = max(longest, streak)
        elif row["defense_action"] == "ENTER":
            streak = 0
    return longest


def _audit(scenario_data: dict[str, Any]) -> dict[str, Any]:
    total = sum(len(data["journal"]) for data in scenario_data.values())
    fails = sum(1 for data in scenario_data.values() for row in data["journal"] if row["lookahead_check"] != "PASS")
    return {
        "checked_trades": total,
        "pass": total - fails,
        "fail": fails,
        "excluded_trades": fails,
        "major_violations": [] if fails == 0 else ["MA lookahead failure detected"],
    }


def _recommendation(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in scenarios if row["lookahead_fail_count"] == 0]
    best = max(candidates, key=lambda row: row["return_mdd_ratio"]) if candidates else {}
    control = next((row for row in scenarios if row["scenario"] == "CONTROL_CURRENT_ROUTER"), {})
    final = "POLICY_ROUTER_CANDIDATE" if best.get("scenario") != "CONTROL_CURRENT_ROUTER" and best.get("return_mdd_ratio", 0) >= control.get("return_mdd_ratio", 0) else "MA_FILTER_REJECTED"
    return {
        "best_scenario": best.get("scenario", "NONE"),
        "final_judgement": final,
        "reason": "MA 필터는 단독 매수가 아니라 쉬어야 할 구간과 감속 구간을 판별하는 보조 입력으로만 평가했습니다.",
    }


def _sample(rows: list[dict[str, Any]], target: int = 220) -> list[dict[str, Any]]:
    if len(rows) <= target:
        return rows
    step = max(1, len(rows) // target)
    sample = rows[::step]
    return sample + ([rows[-1]] if sample[-1] != rows[-1] else [])


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _optional_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def load_true_walk_forward_journal(reports_dir: str | Path = "docs/reports") -> list[dict[str, Any]]:
    path = Path(reports_dir) / "latest_true_walk_forward_summary.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8-sig")).get("journal", [])
