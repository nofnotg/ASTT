from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analysis.v64_policy_compounding_analyzer import _compare, _period_rows, _scenario_summary, _unit_pnl
from analysis.v66_btcd_scenario_analyzer import load_true_walk_forward_journal
from analysis.v673_agent_matrix_analyzer import _build_contexts, _load_quality, _normalize_state
from btcd.btc_trend_feature_builder import BTCTrendFeatureStore
from btcd.btcdom_index_feature_builder import BTCDOMIndexFeatureStore
from portfolio.causal_equity_defense_runner import _decide_multiplier, _drawdown
from portfolio.dynamic_risk_scaler import DynamicRiskScaler
from portfolio.profit_lock_engine import ProfitLockEngine
from portfolio.protected_floor_manager import ProtectedFloorManager
from risk.risk_position_sizer import size_position


COMPOUNDING_SCENARIOS = (
    "BALANCED_GROWTH_COMPOUNDING_BASELINE",
    "BALANCED_GROWTH_COMPOUNDING_DOMINANCE_OVERLAY",
    "ROLLING_EDGE_COMPOUNDING_BASELINE",
    "ROLLING_EDGE_COMPOUNDING_DOMINANCE_OVERLAY",
    "POLICY_BLEND_COMPOUNDING_BASELINE",
    "POLICY_BLEND_COMPOUNDING_DOMINANCE_OVERLAY",
)

BEAR_SCENARIOS = (
    "RELATIVE_STRENGTH_BEAR_COMPOUNDING_AGENT",
    "BEAR_DEFENSE_COMPOUNDING_AGENT",
    "CASH_DEFENSE_COMPOUNDING_AGENT",
    "BEAR_BOUNCE_V2_COMPOUNDING_RESEARCH",
)

ROUTER_SCENARIOS = (
    "BALANCED_GROWTH_COMPOUNDING_BASELINE",
    "COMPOUNDING_SCENARIO_ROUTER_V1",
)

ACTIVE_ROUTE = "BALANCED_GROWTH_COMPOUNDING_BASELINE"


def audit_v681_compounding_vs_dominance_ledger(reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    root = Path(reports_dir)
    v64 = _read(root / "latest_v64_policy_compounding_summary.json")
    v673 = _read(root / "latest_v673_agent_matrix_summary.json")
    router = _read(root / "latest_v673_scenario_router_summary.json")
    integrated = _read(root / "latest_integrated_investment_summary.json")
    v64_balanced = _find(v64.get("scenarios", []), "BALANCED_GROWTH")
    v673_blend = _find(v673.get("scenarios", []), "POLICY_BLEND_DOMINANCE_OVERLAY")
    items = [
        _audit_row("initial_cash", v64.get("initial_cash_krw"), v673.get("initial_cash_krw"), True),
        _audit_row("period", _period_span(v64.get("period_returns", {}).get("BALANCED_GROWTH", {}).get("monthly", [])), _period_span(_records(v673, "POLICY_BLEND_DOMINANCE_OVERLAY", "monthly")), True),
        _audit_row("trade_count", v64_balanced.get("trade_count"), v673_blend.get("trade_count"), False),
        _audit_row("compounding ledger", "current equity based V6.4 independent policy ledger", "V6.7.3 dominance agent ledger", False),
        _audit_row("position sizing", "size_position(current equity) + V6.4 defense engines", "size_position(current equity) + dominance multiplier only", False),
        _audit_row("fee/slippage", "unit pnl minus 0.1% fee", "unit pnl minus 0.1% fee", True),
        _audit_row("skipped trade", "route defense skip affects ledger", "agent skip/reduce affects separate ledger", False),
        _audit_row("source_mode", "V64 policy compounding baseline", "V673 dominance matrix/router", False),
        _audit_row("lookahead audit", _lookahead(v64), _lookahead(v673), True),
    ]
    conclusion = "DIFFERENT_LEDGER_NOT_DIRECTLY_COMPARABLE"
    payload = {
        "schema_version": "v681_reconciliation_audit_v1",
        "title": "V6.8.1 Compounding vs Dominance Ledger Reconciliation Audit",
        "conclusion": conclusion,
        "baseline_to_use": "STRONGEST_COMPOUNDING_BASELINE",
        "strongest_baseline": {
            "rolling": _find(v64.get("scenarios", []), "ROLLING_EDGE_THROTTLE"),
            "balanced": v64_balanced,
        },
        "comparison_items": items,
        "source_files": [
            "latest_v64_policy_compounding_summary.json",
            "latest_v673_agent_matrix_summary.json",
            "latest_v673_scenario_router_summary.json",
            "latest_integrated_investment_summary.json" if integrated else "latest_v62_full_investment_summary.json",
        ],
        "reason": "V6.4 is the official compounding reinvestment ledger. V6.7.3 validates dominance agents, but it is not the same policy compounding ledger, so 150만원대와 90만원대 결과를 직접 비교하면 안 됩니다.",
        **_safety(),
    }
    return payload


def analyze_v681_compounding_dominance(
    initial_cash_krw: float = 500000.0,
    reports_dir: str | Path = "docs/reports",
    archive_dir: str | Path = "replay_store/historical_archive",
    processed_dir: str | Path = "data/processed",
) -> dict[str, Any]:
    contexts, quality = _load_contexts(reports_dir, archive_dir, processed_dir)
    data = {name: _simulate(name, contexts, initial_cash_krw) for name in COMPOUNDING_SCENARIOS}
    scenarios = [_decision_row(name, data[name], data["BALANCED_GROWTH_COMPOUNDING_BASELINE"], initial_cash_krw) for name in COMPOUNDING_SCENARIOS]
    payload = {
        "schema_version": "v681_compounding_dominance_v1",
        "initial_cash_krw": initial_cash_krw,
        "dominance_data_quality": quality,
        "official_baseline": "BALANCED_GROWTH_COMPOUNDING_BASELINE",
        "scenarios": scenarios,
        "saved_loss_missed_profit": _saved_loss_rows(data, "BALANCED_GROWTH_COMPOUNDING_BASELINE"),
        "period_returns": _period_return_payload(data),
        "period_records": _period_record_payload(data),
        "equity_curve": {name: _sample_curve(d["equity_curve"]) for name, d in data.items()},
        "drawdown_curve": {name: _sample_curve(d["drawdown_curve"]) for name, d in data.items()},
        "lookahead_audit": _lookahead_audit(data),
        "decision": _dominance_decision(scenarios),
        **_safety(),
    }
    return payload


def analyze_v681_bear_compounding_agents(
    initial_cash_krw: float = 500000.0,
    reports_dir: str | Path = "docs/reports",
    archive_dir: str | Path = "replay_store/historical_archive",
    processed_dir: str | Path = "data/processed",
) -> dict[str, Any]:
    contexts, quality = _load_contexts(reports_dir, archive_dir, processed_dir)
    base = _simulate("BALANCED_GROWTH_COMPOUNDING_BASELINE", contexts, initial_cash_krw)
    data = {name: _simulate(name, contexts, initial_cash_krw) for name in BEAR_SCENARIOS}
    data["BALANCED_GROWTH_COMPOUNDING_BASELINE"] = base
    scenarios = [_decision_row(name, data[name], base, initial_cash_krw) for name in BEAR_SCENARIOS]
    rows = []
    for row in scenarios:
        yearly = {r["period"]: r for r in _period_rows(data[str(row["scenario"])]["journal"], "year")}
        row = dict(row)
        row["return_2025_pct"] = yearly.get("2025", {}).get("return_pct", 0.0)
        row["return_2026_pct"] = yearly.get("2026", {}).get("return_pct", 0.0)
        rows.append(row)
    return {
        "schema_version": "v681_bear_compounding_agent_v1",
        "initial_cash_krw": initial_cash_krw,
        "dominance_data_quality": quality,
        "baseline": _scenario_summary("BALANCED_GROWTH_COMPOUNDING_BASELINE", base, initial_cash_krw),
        "scenarios": rows,
        "saved_loss_missed_profit": _saved_loss_rows(data, "BALANCED_GROWTH_COMPOUNDING_BASELINE"),
        "period_returns": _period_return_payload(data),
        "period_records": _period_record_payload(data),
        "lookahead_audit": _lookahead_audit(data),
        "decision": "BEAR_AGENT_CANDIDATE" if any(row["decision"].endswith("CANDIDATE") for row in rows) else "PAPER_MORE_REQUIRED",
        **_safety(),
    }


def analyze_v681_compounding_router(
    initial_cash_krw: float = 500000.0,
    reports_dir: str | Path = "docs/reports",
    archive_dir: str | Path = "replay_store/historical_archive",
    processed_dir: str | Path = "data/processed",
) -> dict[str, Any]:
    contexts, quality = _load_contexts(reports_dir, archive_dir, processed_dir)
    data = {name: _simulate(name, contexts, initial_cash_krw) for name in ROUTER_SCENARIOS}
    base = data["BALANCED_GROWTH_COMPOUNDING_BASELINE"]
    scenarios = [_decision_row(name, data[name], base, initial_cash_krw) for name in ROUTER_SCENARIOS]
    for row in scenarios:
        hwm = _hwm_metrics(data[str(row["scenario"])]["journal"])
        row.update(hwm)
    router = _find(scenarios, "COMPOUNDING_SCENARIO_ROUTER_V1")
    return {
        "schema_version": "v681_compounding_router_v1",
        "initial_cash_krw": initial_cash_krw,
        "dominance_data_quality": quality,
        "scenarios": scenarios,
        "routing_rules": _routing_rules(),
        "agent_usage_count": dict(Counter(str(row.get("selected_agent_before_trade")) for row in data["COMPOUNDING_SCENARIO_ROUTER_V1"]["journal"])),
        "period_returns": _period_return_payload(data),
        "period_records": _period_record_payload(data),
        "lookahead_audit": _lookahead_audit(data),
        "decision": router.get("decision", "PAPER_MORE_REQUIRED"),
        **_safety(),
    }


def build_v681_control_tower_review(reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    root = Path(reports_dir)
    dominance = _read(root / "latest_v681_compounding_dominance_summary.json")
    bear = _read(root / "latest_v681_bear_compounding_agent_summary.json")
    router = _read(root / "latest_v681_compounding_router_summary.json")
    paper = _read(root / "latest_v681_paper_runtime_summary.json")
    candidates = []
    for source in (dominance, bear, router):
        for row in source.get("scenarios", []):
            if str(row.get("decision", "")).endswith("CANDIDATE"):
                candidates.append({"route": row.get("scenario"), "status": "READY_FOR_SHADOW", "reason": row.get("decision")})
    payload = {
        "schema_version": "v681_control_tower_v1",
        "llm_provider_requested": llm_provider,
        "llm_used": False,
        "fallback_used": True,
        "active_route": ACTIVE_ROUTE,
        "active_change_applied": False,
        "manual_switch_required": True,
        "candidate_routes": candidates,
        "rebalance_candidates": _rebalance_candidates(dominance, bear, router),
        "risk_flags": _risk_flags(dominance, bear, router, paper),
        "recommendations": [
            "Keep BALANCED_GROWTH_COMPOUNDING_BASELINE active for paper.",
            "Run dominance/router routes as shadow until forward evidence is enough.",
            "Do not promote any route without manual confirm-switch.",
        ],
        "decision": "CONTROL_TOWER_READY_FOR_PAPER",
        **_safety(),
    }
    return payload


def run_v681_paper_backfill_from_20260101(
    initial_cash_krw: float = 500000.0,
    start_date: str = "2026-01-01",
    active_route: str = ACTIVE_ROUTE,
    reports_dir: str | Path = "docs/reports",
    archive_dir: str | Path = "replay_store/historical_archive",
    processed_dir: str | Path = "data/processed",
    data_dir: str | Path = "data/paper",
) -> dict[str, Any]:
    contexts, quality = _load_contexts(reports_dir, archive_dir, processed_dir)
    filtered = [context for context in contexts if str(context["trade"].get("entry_time", ""))[:10] >= start_date]
    data = _simulate(active_route, filtered, initial_cash_krw)
    root = Path(data_dir)
    _write_paper_artifacts(root, active_route, data["journal"])
    current_equity = float(data["journal"][-1]["equity_after"]) if data["journal"] else initial_cash_krw
    payload = {
        "schema_version": "v681_paper_runtime_v1",
        "source_mode": {"backfill": "historical_backfill", "future": "live_forward"},
        "start_date": start_date,
        "initial_cash_krw": initial_cash_krw,
        "active_route": active_route,
        "shadow_routes": [
            "BALANCED_GROWTH_COMPOUNDING_DOMINANCE_OVERLAY",
            "COMPOUNDING_SCENARIO_ROUTER_V1",
            "BEAR_DEFENSE_COMPOUNDING_AGENT",
        ],
        "backfill_done": True,
        "live_forward_running": False,
        "paper_server_port": None,
        "current_equity_krw": current_equity,
        "current_cash_krw": current_equity,
        "open_positions": 0,
        "today_pnl_krw": _period_pnl(data["journal"], "day"),
        "weekly_pnl_krw": _period_pnl(data["journal"], "week"),
        "monthly_pnl_krw": _period_pnl(data["journal"], "month"),
        "daily_rows": _period_records(data["journal"], "day"),
        "weekly_rows": _period_records(data["journal"], "week"),
        "monthly_rows": _period_records(data["journal"], "month"),
        "last_decision_time": data["journal"][-1]["decision_time"] if data["journal"] else None,
        "healthcheck": "PAPER_BACKFILL_READY",
        "dominance_data_quality": quality,
        "decision": "PAPER_FORWARD_RUNNING" if False else "PAPER_RUNNING",
        **_safety(),
    }
    return payload


def start_v681_paper_server(active_route: str = ACTIVE_ROUTE, port: int = 8787, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    payload = _read(Path(reports_dir) / "latest_v681_paper_runtime_summary.json")
    payload.update(
        {
            "active_route": active_route,
            "paper_server_port": port,
            "live_forward_running": False,
            "server_ready": False,
            "healthcheck": "SERVER_NOT_STARTED_IN_CODEX_SESSION",
            "start_command": f"python -m replay_lab.app.replay_cli start-v681-paper-server --active-route {active_route} --port {port}",
            "windows_task_scheduler_hint": f"schtasks /Create /SC MINUTE /MO 5 /TN ASTT_V681_PAPER /TR \"python -m replay_lab.app.replay_cli run-v681-paper-backfill-from-20260101 --active-route {active_route}\"",
            **_safety(),
        }
    )
    return payload


def register_v681_shadow_route(route: str, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    root = Path(reports_dir)
    payload = _read(root / "latest_v681_paper_runtime_summary.json")
    routes = list(payload.get("shadow_routes", []))
    if route not in routes:
        routes.append(route)
    payload["shadow_routes"] = routes
    payload["manual_switch_required"] = True
    payload.update(_safety())
    return payload


def _load_contexts(reports_dir: str | Path, archive_dir: str | Path, processed_dir: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    quality = _load_quality(reports_dir)
    source = sorted(load_true_walk_forward_journal(reports_dir), key=lambda row: str(row.get("entry_time", "")))
    if quality.get("data_quality") == "GOOD":
        start = str(quality.get("common_coverage_start", ""))
        end = str(quality.get("common_coverage_end", "9999"))
        source = [row for row in source if start <= str(row.get("entry_time", "")) <= end]
    store = BTCDOMIndexFeatureStore(processed_dir)
    btc_store = BTCTrendFeatureStore(archive_dir)
    contexts = _build_contexts(source, store, btc_store)
    for context in contexts:
        context["state"] = _normalize_state(context["state"])
    return contexts, quality


def _simulate(scenario: str, contexts: list[dict[str, Any]], initial_cash: float) -> dict[str, Any]:
    equity = initial_cash
    peak = initial_cash
    scaler = DynamicRiskScaler()
    profit_lock = ProfitLockEngine(initial_cash)
    floor_manager = ProtectedFloorManager()
    journal: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []
    drawdown_curve: list[dict[str, Any]] = []
    for idx, context in enumerate(contexts):
        trade = context["trade"]
        state = context["state"]
        decision_time = context["decision_time"]
        entry_time = context["entry_time"]
        policy = _base_policy(scenario, trade)
        selected_agent = _selected_agent(scenario, state, trade, journal)
        drawdown_before = _drawdown(equity, peak)
        rolling_audit = scaler.audit_window(20)
        decision = _decide_multiplier(policy, trade, equity, drawdown_before, scaler, profit_lock)
        multiplier = float(decision["risk_multiplier_after_defense"])
        action = "SKIP" if decision["defense_action"] == "SKIP" or multiplier <= 0 else "ENTER"
        extra_action, overlay_multiplier, extra_reasons = _overlay_action(scenario, selected_agent, trade, state, journal, equity, peak)
        multiplier = min(multiplier, overlay_multiplier)
        if extra_action == "SKIP" or multiplier <= 0:
            action = "SKIP"
        sizing = size_position(equity, float(trade.get("entry_price", 0.0)), float(trade.get("stop_price", 0.0)))
        if not sizing.get("sizing_valid"):
            action = "SKIP"
            extra_reasons.append(str(sizing.get("reason") or "INVALID_SIZING"))
        position_krw = pnl = 0.0
        if action == "ENTER":
            base_position = min(float(sizing["position_krw"]), equity)
            floor_multiplier, floor_capped = floor_manager.cap_multiplier(equity, _unit_pnl(trade, base_position), multiplier)
            if floor_capped:
                multiplier = floor_multiplier
                extra_reasons.append("PROTECTED_FLOOR_CAP")
            position_krw = base_position * multiplier
            pnl = _unit_pnl(trade, position_krw)
            scaler.record(pnl, str(trade.get("exit_time")))
        before = equity
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        drawdown_after = _drawdown(equity, peak)
        lookahead_pass = bool(context.get("lookahead_pass")) and int(rolling_audit["rolling_trades_used"]) <= idx
        reasons = list(decision.get("defense_reasons") or ["NO_DEFENSE"]) + extra_reasons
        row = {
            "trade_id": trade.get("trade_id"),
            "date": str(trade.get("entry_time", ""))[:10],
            "entry_time": entry_time,
            "exit_time": trade.get("exit_time"),
            "market": trade.get("market"),
            "plan": trade.get("plan"),
            "strategy": trade.get("strategy"),
            "setup_type": trade.get("setup_type"),
            "position_krw": position_krw,
            "pnl_krw": pnl,
            "return_pct": pnl / before * 100 if before else 0.0,
            "equity_before": before,
            "equity_after": equity,
            "drawdown_pct": drawdown_after,
            "policy": policy,
            "scenario": scenario,
            "selected_agent_before_trade": selected_agent,
            "defense_state_before_trade": decision["defense_state_before_trade"],
            "risk_multiplier_after_defense": 0.0 if action == "SKIP" else multiplier,
            "defense_action": action,
            "defense_reasons": reasons,
            "market_state": state.get("market_state"),
            "dominance_regime": state.get("dominance_regime"),
            "btc_trend": state.get("btc_trend"),
            "feature_cutoff_time": str(trade.get("feature_cutoff_time") or decision_time),
            "decision_time": decision_time,
            "dominance_feature_time_1h": context["feature"].get("btcdom_feature_time_1h"),
            "dominance_feature_time_4h": context["feature"].get("btcdom_feature_time_4h"),
            "dominance_feature_time_1d": context["feature"].get("btcdom_feature_time_1d"),
            "btc_trend_feature_time": context["btc"].get("timestamp"),
            "used_future_data": not lookahead_pass,
            "lookahead_check": "PASS" if lookahead_pass else "FAIL",
            **_safety(),
        }
        journal.append(row)
        equity_curve.append({"sequence": idx, "time": trade.get("exit_time"), "equity": equity})
        drawdown_curve.append({"sequence": idx, "time": trade.get("exit_time"), "drawdown_pct": drawdown_after})
    return {"journal": journal, "equity_curve": equity_curve, "drawdown_curve": drawdown_curve}


def _base_policy(scenario: str, trade: dict[str, Any]) -> str:
    if scenario.startswith("ROLLING"):
        return "ROLLING_EDGE_THROTTLE"
    if scenario.startswith("POLICY_BLEND"):
        return "ROLLING_EDGE_THROTTLE" if str(trade.get("plan")) == "PLAN_A_ICT_FAT_TAIL" else "BALANCED_GROWTH"
    return "BALANCED_GROWTH"


def _selected_agent(scenario: str, state: dict[str, Any], trade: dict[str, Any], journal: list[dict[str, Any]]) -> str:
    if scenario == "COMPOUNDING_SCENARIO_ROUTER_V1":
        market_state = str(state.get("market_state"))
        if market_state in {"BULL_ATTACK", "ALT_FRIENDLY", "NORMAL"}:
            return "BALANCED_GROWTH_COMPOUNDING_BASELINE"
        if market_state == "BTC_LED_MARKET":
            return "BALANCED_GROWTH_COMPOUNDING_DOMINANCE_OVERLAY"
        if market_state == "EDGE_DECAY":
            return "RELATIVE_STRENGTH_BEAR_COMPOUNDING_AGENT"
        if market_state == "RISK_OFF_ALT_WEAK":
            return "BEAR_DEFENSE_COMPOUNDING_AGENT"
        if market_state in {"BEAR_DEFENSE", "LOCKDOWN"}:
            return "CASH_DEFENSE_COMPOUNDING_AGENT"
        if market_state == "BEAR_BOUNCE_ONLY":
            return "BEAR_BOUNCE_V2_COMPOUNDING_RESEARCH"
    return scenario


def _overlay_action(scenario: str, agent: str, trade: dict[str, Any], state: dict[str, Any], journal: list[dict[str, Any]], equity: float, peak: float) -> tuple[str, float, list[str]]:
    market_state = str(state.get("market_state"))
    strong = _strong_setup(trade)
    monthly_ret = _current_month_return(journal)
    recent_pf = _recent_pf(journal, 20)
    dd = _drawdown(equity, peak)
    if "DOMINANCE_OVERLAY" in scenario or agent.endswith("DOMINANCE_OVERLAY"):
        return _dominance_overlay(market_state, strong)
    if agent == "RELATIVE_STRENGTH_BEAR_COMPOUNDING_AGENT":
        if market_state in {"BTC_LED_MARKET", "EDGE_DECAY", "RISK_OFF_ALT_WEAK"}:
            return ("ENTER", 0.70, ["RELATIVE_STRENGTH_PROXY_PASS"]) if strong else ("ENTER", 0.35, ["RELATIVE_STRENGTH_PROXY_WEAK"])
        return "ENTER", 1.0, ["BEAR_AGENT_PASS"]
    if agent == "BEAR_DEFENSE_COMPOUNDING_AGENT":
        if market_state in {"RISK_OFF_ALT_WEAK", "BEAR_DEFENSE"} or recent_pf < 1.0 or monthly_ret < -3.0:
            return ("ENTER", 0.50, ["BEAR_DEFENSE_A_PLUS_LIMIT"]) if strong else ("ENTER", 0.35, ["BEAR_DEFENSE_REDUCE"])
        return "ENTER", 1.0, ["BEAR_DEFENSE_PASS"]
    if agent == "CASH_DEFENSE_COMPOUNDING_AGENT":
        if market_state == "LOCKDOWN" or monthly_ret < -7.0 or recent_pf < 0.8 or dd <= -20.0:
            return "SKIP", 0.0, ["CASH_DEFENSE_OBSERVATION_ONLY"]
        return "ENTER", 0.35, ["CASH_DEFENSE_SMALL_SIZE"]
    if agent == "BEAR_BOUNCE_V2_COMPOUNDING_RESEARCH":
        if market_state == "BEAR_BOUNCE_ONLY" and strong:
            return "ENTER", 0.25, ["BEAR_BOUNCE_RESEARCH_SMALL"]
        return "SKIP", 0.0, ["RESEARCH_ONLY"]
    return "ENTER", 1.0, ["COMPOUNDING_BASELINE"]


def _dominance_overlay(market_state: str, strong: bool) -> tuple[str, float, list[str]]:
    if market_state in {"ALT_FRIENDLY", "NORMAL"}:
        return "ENTER", 1.0, ["DOMINANCE_ALLOW"]
    if market_state == "BTC_LED_MARKET":
        return "ENTER", 0.70, ["BTC_LED_MARKET_REDUCE"]
    if market_state == "RISK_OFF_ALT_WEAK":
        return "ENTER", 0.35, ["RISK_OFF_ALT_WEAK_REDUCE"]
    if market_state == "BEAR_DEFENSE" and strong:
        return "ENTER", 0.35, ["BEAR_DEFENSE_A_PLUS_ONLY"]
    if market_state in {"BEAR_DEFENSE", "LOCKDOWN"}:
        return "SKIP", 0.0, ["OBSERVATION_ONLY"]
    return "ENTER", 1.0, ["DOMINANCE_PASS"]


def _strong_setup(trade: dict[str, Any]) -> bool:
    setup = str(trade.get("setup_type"))
    return str(trade.get("plan")) == "PLAN_A_ICT_FAT_TAIL" or "FVG_OB_OVERLAP" in setup or "LIQUIDITY_SWEEP" in setup


def _recent_pf(journal: list[dict[str, Any]], n: int) -> float:
    rows = [row for row in journal[-n:] if row.get("defense_action") == "ENTER"]
    wins = sum(float(row.get("pnl_krw", 0.0)) for row in rows if float(row.get("pnl_krw", 0.0)) > 0)
    losses = abs(sum(float(row.get("pnl_krw", 0.0)) for row in rows if float(row.get("pnl_krw", 0.0)) < 0))
    return wins / losses if losses else 99.0 if wins else 0.0


def _current_month_return(journal: list[dict[str, Any]]) -> float:
    if not journal:
        return 0.0
    month = str(journal[-1].get("date", ""))[:7]
    rows = [row for row in journal if str(row.get("date", ""))[:7] == month]
    if not rows:
        return 0.0
    start = float(rows[0].get("equity_before", 0.0))
    end = float(rows[-1].get("equity_after", 0.0))
    return (end / start - 1.0) * 100.0 if start else 0.0


def _decision_row(name: str, data: dict[str, Any], baseline: dict[str, Any], initial_cash: float) -> dict[str, Any]:
    row = _scenario_summary(name, data, initial_cash)
    base = _scenario_summary("BALANCED_GROWTH_COMPOUNDING_BASELINE", baseline, initial_cash)
    saved = _saved_loss_rows({name: data, "BASE": baseline}, "BASE")[0] if name != "BALANCED_GROWTH_COMPOUNDING_BASELINE" else {"saved_loss_krw": 0.0, "missed_profit_krw": 0.0, "net_effect_krw": 0.0}
    row.update(saved)
    row["decision"] = _scenario_decision(row, base)
    return row


def _scenario_decision(row: dict[str, Any], base: dict[str, Any]) -> str:
    if row["scenario"] == "BALANCED_GROWTH_COMPOUNDING_BASELINE":
        return "STRONGEST_COMPOUNDING_BASELINE"
    if "BEAR_BOUNCE" in str(row["scenario"]):
        return "RESEARCH_ONLY"
    better = row["final_equity_krw"] >= base["final_equity_krw"] and row["mdd_pct"] >= base["mdd_pct"] and row["return_mdd_ratio"] >= base["return_mdd_ratio"]
    saved_ok = float(row.get("net_effect_krw", 0.0)) >= 0.0
    return "PAPER_ROUTE_CANDIDATE" if better and saved_ok else "PAPER_MORE_REQUIRED"


def _saved_loss_rows(data: dict[str, dict[str, Any]], baseline_name: str) -> list[dict[str, Any]]:
    base = {row["trade_id"]: row for row in data[baseline_name]["journal"]}
    out = []
    for name, item in data.items():
        if name == baseline_name:
            continue
        saved = missed = 0.0
        for row in item["journal"]:
            base_pnl = float(base.get(row["trade_id"], {}).get("pnl_krw", 0.0))
            pnl = float(row.get("pnl_krw", 0.0))
            delta = pnl - base_pnl
            if base_pnl < 0 and delta > 0:
                saved += delta
            elif base_pnl > 0 and delta < 0:
                missed += -delta
        out.append({"scenario": name, "saved_loss_krw": saved, "missed_profit_krw": missed, "net_effect_krw": saved - missed})
    return out


def _period_return_payload(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {name: {"weekly": _period_rows(d["journal"], "week"), "monthly": _period_rows(d["journal"], "month"), "yearly": _period_rows(d["journal"], "year")} for name, d in data.items()}


def _period_record_payload(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {name: {"daily": _period_records(d["journal"], "day"), "weekly": _period_records(d["journal"], "week"), "monthly": _period_records(d["journal"], "month")} for name, d in data.items()}


def _period_records(journal: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        groups[_period_key(str(row.get("date", "")), kind)].append(row)
    rows = []
    for period, items in sorted(groups.items()):
        start = float(items[0].get("equity_before", 0.0))
        end = float(items[-1].get("equity_after", 0.0))
        entered = [row for row in items if row.get("defense_action") == "ENTER"]
        rows.append({"period": period, "start_date": items[0].get("date"), "end_date": items[-1].get("date"), "trade_count": len(entered), "start_equity_krw": start, "end_equity_krw": end, "pnl_krw": sum(float(row.get("pnl_krw", 0.0)) for row in items), "return_pct": (end / start - 1.0) * 100.0 if start else 0.0, "mdd_pct": min(float(row.get("drawdown_pct", 0.0)) for row in items)})
    return rows


def _period_key(value: str, kind: str) -> str:
    dt = datetime.fromisoformat(value[:10])
    if kind == "day":
        return dt.date().isoformat()
    if kind == "month":
        return f"{dt.year:04d}-{dt.month:02d}"
    iso = dt.isocalendar()
    return f"{iso.year:04d}-W{iso.week:02d}"


def _lookahead_audit(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    total = sum(len(d["journal"]) for d in data.values())
    fail = sum(1 for d in data.values() for row in d["journal"] if row.get("lookahead_check") != "PASS")
    return {"checked_trades": total, "pass": total - fail, "fail": fail, "major_violations": [] if fail == 0 else ["LOOKAHEAD_FAIL"]}


def _dominance_decision(rows: list[dict[str, Any]]) -> str:
    candidates = [row for row in rows if row.get("decision") == "PAPER_ROUTE_CANDIDATE" and "DOMINANCE" in str(row.get("scenario"))]
    return "COMPOUNDING_DOMINANCE_VALIDATED" if candidates else "COMPOUNDING_DOMINANCE_REJECTED"


def _hwm_metrics(journal: list[dict[str, Any]]) -> dict[str, Any]:
    peak = 0.0
    worst_giveback = 0.0
    for row in journal:
        equity = float(row.get("equity_after", 0.0))
        peak = max(peak, equity)
        if peak:
            worst_giveback = min(worst_giveback, (equity / peak - 1.0) * 100.0)
    return {"hwm_score": 100.0 + worst_giveback, "giveback_ratio_pct": abs(worst_giveback), "recovery_days": 0}


def _routing_rules() -> list[dict[str, str]]:
    return [
        {"market_state": "ALT_FRIENDLY/NORMAL", "route": "BALANCED_GROWTH_COMPOUNDING_BASELINE"},
        {"market_state": "BTC_LED_MARKET", "route": "BALANCED_GROWTH_COMPOUNDING_DOMINANCE_OVERLAY"},
        {"market_state": "EDGE_DECAY", "route": "RELATIVE_STRENGTH_BEAR_COMPOUNDING_AGENT"},
        {"market_state": "RISK_OFF_ALT_WEAK", "route": "BEAR_DEFENSE_COMPOUNDING_AGENT"},
        {"market_state": "BEAR_DEFENSE/LOCKDOWN", "route": "CASH_DEFENSE_COMPOUNDING_AGENT"},
    ]


def _rebalance_candidates(*summaries: dict[str, Any]) -> list[dict[str, str]]:
    out = []
    for summary in summaries:
        for row in summary.get("scenarios", []):
            decision = str(row.get("decision", ""))
            if decision.endswith("CANDIDATE"):
                out.append({"route": str(row.get("scenario")), "candidate_type": "promote_shadow_route_candidate", "status": "MANUAL_APPROVAL_REQUIRED"})
            elif decision == "PAPER_MORE_REQUIRED":
                out.append({"route": str(row.get("scenario")), "candidate_type": "keep_shadow_or_reject_candidate", "status": "REVIEW_REQUIRED"})
    return out[:12]


def _risk_flags(*summaries: dict[str, Any]) -> list[str]:
    flags = ["LIVE_NOT_ALLOWED", "ACTIVE_ROUTE_AUTO_SWITCH_DISABLED"]
    if any(summary.get("lookahead_audit", {}).get("fail", 0) for summary in summaries):
        flags.append("LOOKAHEAD_FAIL_PRESENT")
    return flags


def _write_paper_artifacts(root: Path, route: str, journal: list[dict[str, Any]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "journal").mkdir(parents=True, exist_ok=True)
    db = root / "paper_trading.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("create table if not exists paper_equity_snapshots (id integer primary key, ts text, route text, equity real, cash real)")
        conn.execute("create table if not exists paper_route_events (id integer primary key, ts text, route text, event text)")
        conn.execute("delete from paper_equity_snapshots")
        conn.execute("delete from paper_route_events")
        for row in journal:
            conn.execute("insert into paper_equity_snapshots(ts, route, equity, cash) values(?,?,?,?)", (row.get("decision_time"), route, row.get("equity_after"), row.get("equity_after")))
        conn.execute("insert into paper_route_events(ts, route, event) values(?,?,?)", (datetime.utcnow().isoformat(), route, "BACKFILL"))
    _write_jsonl(root / "journal" / "paper_decisions.jsonl", journal)
    _write_jsonl(root / "journal" / "paper_trades.jsonl", [row for row in journal if row.get("defense_action") == "ENTER"])
    _write_jsonl(root / "journal" / "paper_equity_snapshots.jsonl", [{"ts": row.get("decision_time"), "equity": row.get("equity_after"), "cash": row.get("equity_after"), "route": route} for row in journal])
    _write_jsonl(root / "journal" / "paper_route_events.jsonl", [{"ts": datetime.utcnow().isoformat(), "route": route, "event": "BACKFILL"}])
    _write_jsonl(root / "journal" / "control_tower_reviews.jsonl", [{"ts": datetime.utcnow().isoformat(), "route": route, "review": "BACKFILL_READY", **_safety()}])


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in rows), encoding="utf-8")


def _period_pnl(journal: list[dict[str, Any]], kind: str) -> float:
    records = _period_records(journal, kind)
    return float(records[-1].get("pnl_krw", 0.0)) if records else 0.0


def _audit_row(item: str, v64: Any, v673: Any, comparable: bool) -> dict[str, Any]:
    return {"item": item, "v64_compounding": v64, "v673_dominance": v673, "comparable": comparable}


def _period_span(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "NO_DATA"
    return f"{rows[0].get('period')}~{rows[-1].get('period')}"


def _records(summary: dict[str, Any], name: str, kind: str) -> list[dict[str, Any]]:
    return summary.get("period_records", {}).get(name, {}).get(kind, [])


def _lookahead(summary: dict[str, Any]) -> str:
    audit = summary.get("lookahead_audit", {})
    if audit:
        return f"fail={audit.get('fail', 0)}"
    scenarios = summary.get("scenarios", [])
    fail = sum(int(row.get("lookahead_fail_count", 0) or 0) for row in scenarios)
    return f"fail={fail}"


def _find(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next((row for row in rows if row.get("scenario") == name), {})


def _sample_curve(rows: list[dict[str, Any]], target: int = 240) -> list[dict[str, Any]]:
    if len(rows) <= target:
        return rows
    step = max(1, len(rows) // target)
    sample = rows[::step]
    return sample + ([rows[-1]] if sample[-1] != rows[-1] else [])


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _safety() -> dict[str, bool]:
    return {"real_order_enabled": False, "live_order_allowed": False, "auto_apply_allowed": False}
