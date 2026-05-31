from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from analysis.v64_policy_compounding_analyzer import _unit_pnl
from analysis.v681_compounding_control_tower import _drawdown, _load_contexts, _recent_pf, _safety, _strong_setup
from bear_response.bear_bounce_score import score_bear_bounce
from portfolio.causal_equity_defense_runner import _decide_multiplier
from portfolio.dynamic_risk_scaler import DynamicRiskScaler
from portfolio.profit_lock_engine import ProfitLockEngine
from portfolio.protected_floor_manager import ProtectedFloorManager
from risk.risk_position_sizer import size_position


SCENARIOS = (
    "ACTIVE_BASELINE",
    "LOSS_GUARD_2026_ROUTER_V1_SHADOW",
    "BEAR_DEFENSE_ONLY",
    "BEAR_BOUNCE_PROFIT_AGENT",
    "BEAR_DEFENSE_PLUS_BOUNCE",
    "FULL_BEAR_RESPONSE_ROUTER",
)


def analyze_v682_bear_defense_deep_insight(
    initial_cash_krw: float = 500000.0,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
    processed_dir: str = "data/processed",
) -> dict[str, Any]:
    contexts, quality = _load_contexts(reports_dir, archive_dir, processed_dir)
    configs = _loss_guard_sensitivity_configs()
    rows = []
    for config in configs:
        data = _simulate("ACTIVE_BASELINE", contexts, initial_cash_krw, loss_guard_config=config)
        row = _summary(config["name"], data["journal"], initial_cash_krw)
        row["config"] = {key: value for key, value in config.items() if key != "name"}
        rows.append(row)
    baseline = _simulate("ACTIVE_BASELINE", contexts, initial_cash_krw, loss_guard_config=_active_config(False))
    active = _simulate("ACTIVE_BASELINE", contexts, initial_cash_krw, loss_guard_config=_active_config(True))
    insight = _guard_activation_insight(active["journal"])
    return {
        "schema_version": "v682_bear_defense_deep_insight_v1",
        "initial_cash_krw": initial_cash_krw,
        "dominance_data_quality": quality,
        "baseline": _summary("BASE_BALANCED_PROXY", baseline["journal"], initial_cash_krw),
        "active_candidate": _summary("LG_V2_BALANCED_PLUS_DOM_GATE", active["journal"], initial_cash_krw),
        "sensitivity_rows": sorted(rows, key=lambda row: row["return_mdd_ratio"], reverse=True),
        "guard_activation": insight,
        "decision": "BEAR_DEFENSE_INSIGHT_READY",
        **_safety(),
    }


def analyze_v682_bear_bounce_profit(
    initial_cash_krw: float = 500000.0,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
    processed_dir: str = "data/processed",
) -> dict[str, Any]:
    contexts, quality = _load_contexts(reports_dir, archive_dir, processed_dir)
    data = _simulate("BEAR_BOUNCE_PROFIT_AGENT", contexts, initial_cash_krw)
    summary = _summary("BEAR_BOUNCE_PROFIT_AGENT", data["journal"], initial_cash_krw)
    bounce = _bounce_stats(data["journal"])
    return {
        "schema_version": "v682_bear_bounce_profit_v1",
        "initial_cash_krw": initial_cash_krw,
        "dominance_data_quality": quality,
        "scenario": summary,
        "bounce_metrics": bounce,
        "best_bounce_cases": _case_rows(data["journal"], best=True),
        "worst_bounce_cases": _case_rows(data["journal"], best=False),
        "missed_bounce_cases": _missed_bounce_rows(data["journal"]),
        "false_bounce_cases": _false_bounce_rows(data["journal"]),
        "decision": "BEAR_BOUNCE_CANDIDATE" if bounce["net_bounce_pnl_krw"] > 0 and bounce["bounce_entries"] >= 10 else "BEAR_BOUNCE_REJECTED",
        **_safety(),
    }


def analyze_v682_bear_response_router(
    initial_cash_krw: float = 500000.0,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
    processed_dir: str = "data/processed",
) -> dict[str, Any]:
    contexts, quality = _load_contexts(reports_dir, archive_dir, processed_dir)
    data = {name: _simulate(name, contexts, initial_cash_krw) for name in SCENARIOS}
    rows = []
    baseline = _summary("ACTIVE_BASELINE", data["ACTIVE_BASELINE"]["journal"], initial_cash_krw)
    for name in SCENARIOS:
        row = _summary(name, data[name]["journal"], initial_cash_krw)
        row.update(_year_returns(data[name]["journal"]))
        row.update(_saved_loss(data[name]["journal"], data["ACTIVE_BASELINE"]["journal"]))
        row.update(_hwm_metrics(data[name]["journal"], initial_cash_krw))
        row["bounce_trade_count"] = _bounce_stats(data[name]["journal"])["bounce_entries"]
        row["decision"] = _scenario_decision(row, baseline)
        rows.append(row)
    router = next(row for row in rows if row["scenario"] == "FULL_BEAR_RESPONSE_ROUTER")
    return {
        "schema_version": "v682_bear_response_router_v1",
        "initial_cash_krw": initial_cash_krw,
        "dominance_data_quality": quality,
        "scenarios": rows,
        "monthly_returns": {name: _period_rows(data[name]["journal"], "month") for name in SCENARIOS},
        "bounce_metrics": {name: _bounce_stats(data[name]["journal"]) for name in SCENARIOS},
        "route_usage_count": dict(Counter(row.get("selected_route") for row in data["FULL_BEAR_RESPONSE_ROUTER"]["journal"])),
        "proposed_active_route": "LG_V2_BALANCED_PLUS_DOM_GATE",
        "shadow_routes": ["LOSS_GUARD_2026_ROUTER_V1_SHADOW", "BEAR_BOUNCE_PROFIT_AGENT", "FULL_BEAR_RESPONSE_ROUTER"],
        "active_route_change_applied": False,
        "decision": router["decision"] if router["decision"].endswith("CANDIDATE") else "PAPER_MORE_REQUIRED",
        **_safety(),
    }


def build_v682_bounce_case_study(
    reports_dir: str = "docs/reports",
    initial_cash_krw: float = 500000.0,
) -> dict[str, Any]:
    payload = analyze_v682_bear_bounce_profit(initial_cash_krw, reports_dir)
    return {
        "schema_version": "v682_bounce_case_study_v1",
        "best_bounce_cases": payload["best_bounce_cases"],
        "worst_bounce_cases": payload["worst_bounce_cases"],
        "missed_bounce_cases": payload["missed_bounce_cases"],
        "false_bounce_cases": payload["false_bounce_cases"],
        "decision": payload["decision"],
        **_safety(),
    }


def register_v682_shadow_route(route: str, reports_dir: str = "docs/reports") -> dict[str, Any]:
    allowed = {"BEAR_BOUNCE_PROFIT_AGENT", "FULL_BEAR_RESPONSE_ROUTER", "LOSS_GUARD_2026_ROUTER_V1_SHADOW"}
    status = "SHADOW_ROUTE_READY" if route in allowed else "PAPER_MORE_REQUIRED"
    return {
        "schema_version": "v682_shadow_route_registration_v1",
        "route": route,
        "status": status,
        "active_route_change_applied": False,
        "manual_switch_required": True,
        "reports_dir": reports_dir,
        "decision": status,
        **_safety(),
    }


def _simulate(
    scenario: str,
    contexts: list[dict[str, Any]],
    initial_cash: float,
    *,
    loss_guard_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    equity = initial_cash
    peak = initial_cash
    scaler = DynamicRiskScaler()
    profit_lock = ProfitLockEngine(initial_cash)
    floor_manager = ProtectedFloorManager()
    journal: list[dict[str, Any]] = []
    cfg = loss_guard_config or _active_config(True)
    for idx, context in enumerate(contexts):
        trade = context["trade"]
        state = context["state"]
        before = equity
        dd_before = _drawdown(equity, peak)
        route = _selected_route(scenario, context, journal, equity, peak)
        policy = _policy_for_route(route)
        decision = _decide_multiplier(policy, trade, equity, dd_before, scaler, profit_lock)
        multiplier = float(decision["risk_multiplier_after_defense"])
        action = "SKIP" if decision["defense_action"] == "SKIP" or multiplier <= 0.0 else "ENTER"
        reasons = list(decision.get("defense_reasons") or [])
        guard = _guard_state(journal, equity, peak, cfg)

        if route in {"ACTIVE_BASELINE", "LOSS_GUARD_2026_ROUTER_V1_SHADOW", "BEAR_DEFENSE_ONLY", "BEAR_DEFENSE_PLUS_BOUNCE", "FULL_BEAR_RESPONSE_ROUTER"}:
            action, multiplier, guard_reasons = _apply_loss_guard(action, multiplier, trade, state, guard, cfg, route)
            reasons.extend(guard_reasons)

        bounce = score_bear_bounce(context, journal, guard_on=guard["guard_on"], hard_guard=guard["hard_guard"], drawdown_pct=dd_before)
        bounce_entry = False
        if route == "BEAR_BOUNCE_PROFIT_AGENT":
            action, multiplier, bounce_entry = _bounce_only_decision(bounce, guard)
            reasons.append("BEAR_BOUNCE_ONLY")
        elif route in {"BEAR_DEFENSE_PLUS_BOUNCE", "FULL_BEAR_RESPONSE_ROUTER"}:
            action, multiplier, bounce_entry = _maybe_add_bounce(action, multiplier, bounce, guard)
            if bounce_entry:
                reasons.append("BEAR_BOUNCE_SMALL_ENTRY")

        sizing = size_position(equity, float(trade.get("entry_price", 0.0)), float(trade.get("stop_price", 0.0)))
        position_krw = 0.0
        pnl = 0.0
        if not sizing.get("sizing_valid"):
            action = "SKIP"
            multiplier = 0.0
            reasons.append(str(sizing.get("reason") or "INVALID_SIZING"))
        if action == "ENTER":
            base_position = min(float(sizing["position_krw"]), equity)
            floor_multiplier, floor_capped = floor_manager.cap_multiplier(equity, _unit_pnl(trade, base_position), multiplier)
            if floor_capped:
                multiplier = floor_multiplier
                reasons.append("PROTECTED_FLOOR_CAP")
            position_krw = base_position * multiplier
            pnl = _unit_pnl(trade, position_krw)
            scaler.record(pnl, str(trade.get("exit_time")))
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        dd_after = _drawdown(equity, peak)
        lookahead_pass = bool(context.get("lookahead_pass")) and str(trade.get("feature_cutoff_time") or context.get("decision_time")) <= str(context.get("decision_time")) <= str(context.get("entry_time"))
        journal.append(
            {
                "trade_id": trade.get("trade_id"),
                "date": str(trade.get("entry_time", ""))[:10],
                "decision_time": context.get("decision_time"),
                "feature_cutoff_time": str(trade.get("feature_cutoff_time") or context.get("decision_time")),
                "bounce_signal_time": context.get("decision_time"),
                "entry_time": context.get("entry_time"),
                "exit_time": trade.get("exit_time"),
                "market": trade.get("market"),
                "plan": trade.get("plan"),
                "setup_type": trade.get("setup_type"),
                "market_state": state.get("market_state"),
                "dominance_regime": state.get("dominance_regime"),
                "selected_route": route,
                "scenario": scenario,
                "position_krw": position_krw,
                "pnl_krw": pnl,
                "return_pct": pnl / before * 100.0 if before else 0.0,
                "equity_before": before,
                "equity_after": equity,
                "drawdown_before_pct": dd_before,
                "drawdown_pct": dd_after,
                "defense_action": action,
                "risk_multiplier_after_defense": 0.0 if action == "SKIP" else multiplier,
                "guard_on": guard["guard_on"],
                "hard_guard": guard["hard_guard"],
                "current_month_return_pct": guard["month_return_pct"],
                "recent_pf": guard["recent_pf"],
                "bounce_entry": bounce_entry and action == "ENTER",
                **bounce,
                "defense_reasons": reasons or ["NO_DEFENSE"],
                "used_future_data": not lookahead_pass,
                "lookahead_check": "PASS" if lookahead_pass else "FAIL",
                **_safety(),
            }
        )
    return {"journal": journal}


def _selected_route(scenario: str, context: dict[str, Any], journal: list[dict[str, Any]], equity: float, peak: float) -> str:
    if scenario != "FULL_BEAR_RESPONSE_ROUTER":
        return scenario
    market_state = str(context.get("state", {}).get("market_state") or "")
    if market_state in {"BULL_ATTACK", "ALT_FRIENDLY", "NORMAL"}:
        return "ACTIVE_BASELINE"
    if market_state == "BTC_LED_MARKET":
        return "ACTIVE_BASELINE"
    if market_state == "EDGE_DECAY":
        return "LOSS_GUARD_2026_ROUTER_V1_SHADOW"
    if market_state == "RISK_OFF_ALT_WEAK":
        return "BEAR_DEFENSE_ONLY"
    if market_state == "BEAR_DEFENSE":
        return "BEAR_DEFENSE_PLUS_BOUNCE"
    if market_state == "BEAR_BOUNCE_ONLY":
        return "BEAR_BOUNCE_PROFIT_AGENT"
    if market_state == "LOCKDOWN":
        return "OBSERVE_ONLY"
    guard = _guard_state(journal, equity, peak, _active_config(True))
    return "BEAR_DEFENSE_PLUS_BOUNCE" if guard["hard_guard"] else "ACTIVE_BASELINE"


def _policy_for_route(route: str) -> str:
    if route in {"LOSS_GUARD_2026_ROUTER_V1_SHADOW"}:
        return "ROLLING_EDGE_THROTTLE"
    return "BALANCED_GROWTH"


def _guard_state(journal: list[dict[str, Any]], equity: float, peak: float, cfg: dict[str, Any]) -> dict[str, Any]:
    month_return = _current_month_return(journal)
    recent_pf = _recent_pf(journal, int(cfg.get("pf_window", 20)))
    entered = [row for row in journal[-int(cfg.get("pf_window", 20)) :] if row.get("defense_action") == "ENTER"]
    dd = _drawdown(equity, peak)
    pf_bad = len(entered) >= int(cfg.get("min_pf_trades", 20)) and recent_pf < float(cfg["pf_threshold"])
    month_bad = month_return <= float(cfg["month_loss_threshold"])
    dd_bad = dd <= float(cfg["dd_threshold"])
    return {
        "guard_on": bool(month_bad or pf_bad or dd_bad),
        "hard_guard": bool(month_bad and pf_bad),
        "month_return_pct": month_return,
        "recent_pf": recent_pf,
        "drawdown_pct": dd,
        "pf_bad": pf_bad,
        "month_bad": month_bad,
        "dd_bad": dd_bad,
    }


def _apply_loss_guard(
    action: str,
    multiplier: float,
    trade: dict[str, Any],
    state: dict[str, Any],
    guard: dict[str, Any],
    cfg: dict[str, Any],
    route: str,
) -> tuple[str, float, list[str]]:
    reasons: list[str] = []
    if route == "BEAR_DEFENSE_ONLY" and str(state.get("market_state")) in {"RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "LOCKDOWN"}:
        multiplier = min(multiplier, 0.35)
        reasons.append("BEAR_DEFENSE_MARKET_CAP")
    if not guard["guard_on"]:
        return action, multiplier, reasons
    strong = _strong_setup(trade)
    non_plan_a = str(trade.get("plan")) != "PLAN_A_ICT_FAT_TAIL"
    dominance_risk = str(state.get("market_state")) in {"BTC_LED_MARKET", "RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "LOCKDOWN"}
    if dominance_risk and bool(cfg.get("dominance_gate", False)):
        multiplier = min(multiplier, 0.70 if strong else 0.35)
        reasons.append("DOMINANCE_SECONDARY_RISK_GATE")
    if non_plan_a:
        if guard["hard_guard"] and bool(cfg.get("hard_cash", True)):
            action = "SKIP"
            multiplier = 0.0
            reasons.append("HARD_GUARD_SKIP_NON_PLAN_A")
        else:
            multiplier = min(multiplier, float(cfg["cap"]))
            reasons.append("LOSS_GUARD_CAP_NON_PLAN_A")
    elif strong and dominance_risk:
        multiplier = min(multiplier, 0.70)
        reasons.append("PLAN_A_DOMINANCE_RISK_CAP")
    else:
        reasons.append("PLAN_A_PRESERVED")
    return action, multiplier, reasons


def _bounce_only_decision(bounce: dict[str, Any], guard: dict[str, Any]) -> tuple[str, float, bool]:
    if guard["hard_guard"] and not bounce["bear_bounce_high_confidence"]:
        return "SKIP", 0.0, False
    if bounce["bear_bounce_high_confidence"]:
        return "ENTER", 0.35, True
    if bounce["bear_bounce_candidate"]:
        return "ENTER", 0.25, True
    return "SKIP", 0.0, False


def _maybe_add_bounce(action: str, multiplier: float, bounce: dict[str, Any], guard: dict[str, Any]) -> tuple[str, float, bool]:
    if guard["hard_guard"] and not bounce["bear_bounce_high_confidence"]:
        return action, multiplier, False
    if bounce["bear_bounce_high_confidence"]:
        return "ENTER", max(min(multiplier, 0.35), 0.25), True
    if action == "SKIP" and bounce["bear_bounce_candidate"]:
        return "ENTER", 0.25, True
    return action, multiplier, False


def _summary(name: str, journal: list[dict[str, Any]], initial_cash: float) -> dict[str, Any]:
    final = float(journal[-1]["equity_after"]) if journal else initial_cash
    entered = [row for row in journal if row.get("defense_action") == "ENTER"]
    pnls = [float(row.get("pnl_krw", 0.0)) for row in entered]
    wins = sum(pnl for pnl in pnls if pnl > 0.0)
    losses = abs(sum(pnl for pnl in pnls if pnl < 0.0))
    mdd = min([0.0] + [float(row.get("drawdown_pct", 0.0)) for row in journal])
    return_pct = (final / initial_cash - 1.0) * 100.0 if initial_cash else 0.0
    return {
        "scenario": name,
        "initial_cash_krw": initial_cash,
        "final_equity_krw": final,
        "return_pct": return_pct,
        "mdd_pct": mdd,
        "profit_factor": wins / losses if losses else 99.0 if wins else 0.0,
        "return_mdd_ratio": return_pct / abs(mdd) if mdd else 0.0,
        "trade_count": len(entered),
        "skipped_trade_count": len(journal) - len(entered),
        "win_rate_pct": sum(1 for pnl in pnls if pnl > 0.0) / len(entered) * 100.0 if entered else 0.0,
        "average_multiplier": sum(float(row.get("risk_multiplier_after_defense", 0.0)) for row in entered) / len(entered) if entered else 0.0,
        "lookahead_fail_count": sum(1 for row in journal if row.get("lookahead_check") != "PASS"),
    }


def _period_rows(journal: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    key_len = {"day": 10, "month": 7, "year": 4}[mode]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        groups[str(row.get("date", ""))[:key_len]].append(row)
    rows = []
    for period in sorted(groups):
        items = groups[period]
        start = float(items[0]["equity_before"])
        end = float(items[-1]["equity_after"])
        rows.append(
            {
                "period": period,
                "trade_count": sum(1 for item in items if item.get("defense_action") == "ENTER"),
                "start_equity_krw": start,
                "end_equity_krw": end,
                "pnl_krw": end - start,
                "return_pct": (end / start - 1.0) * 100.0 if start else 0.0,
                "mdd_pct": min([0.0] + [float(item.get("drawdown_pct", 0.0)) for item in items]),
            }
        )
    return rows


def _current_month_return(journal: list[dict[str, Any]]) -> float:
    if not journal:
        return 0.0
    month = str(journal[-1].get("date", ""))[:7]
    rows = [row for row in journal if str(row.get("date", ""))[:7] == month]
    start = float(rows[0].get("equity_before", 0.0)) if rows else 0.0
    end = float(rows[-1].get("equity_after", 0.0)) if rows else 0.0
    return (end / start - 1.0) * 100.0 if start else 0.0


def _year_returns(journal: list[dict[str, Any]]) -> dict[str, float]:
    rows = _period_rows(journal, "year")
    return {f"return_{row['period']}_pct": row["return_pct"] for row in rows if row["period"] in {"2025", "2026"}}


def _saved_loss(journal: list[dict[str, Any]], baseline: list[dict[str, Any]]) -> dict[str, float]:
    saved = missed = 0.0
    for row, base in zip(journal, baseline):
        pnl = float(row.get("pnl_krw", 0.0))
        base_pnl = float(base.get("pnl_krw", 0.0))
        diff = pnl - base_pnl
        if base_pnl < 0.0 and diff > 0.0:
            saved += diff
        elif base_pnl > 0.0 and diff < 0.0:
            missed += abs(diff)
    return {"saved_loss_krw": saved, "missed_profit_krw": missed, "net_effect_krw": saved - missed}


def _hwm_metrics(journal: list[dict[str, Any]], initial_cash: float) -> dict[str, float]:
    final = float(journal[-1]["equity_after"]) if journal else initial_cash
    peak = max([initial_cash] + [float(row["equity_after"]) for row in journal])
    giveback = peak - final
    total_profit = max(0.0, peak - initial_cash)
    return {
        "high_watermark_krw": peak,
        "profit_giveback_krw": giveback,
        "profit_giveback_ratio_pct": giveback / total_profit * 100.0 if total_profit else 0.0,
        "high_watermark_score": (final / peak * 100.0) if peak else 0.0,
    }


def _bounce_stats(journal: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in journal if row.get("bear_bounce_candidate")]
    entries = [row for row in journal if row.get("bounce_entry")]
    pnls = [float(row.get("pnl_krw", 0.0)) for row in entries]
    return {
        "bounce_candidates": len(candidates),
        "bounce_entries": len(entries),
        "bounce_win_rate_pct": sum(1 for pnl in pnls if pnl > 0.0) / len(entries) * 100.0 if entries else 0.0,
        "avg_bounce_pnl_krw": sum(pnls) / len(entries) if entries else 0.0,
        "net_bounce_pnl_krw": sum(pnls),
        "best_bounce_krw": max(pnls) if pnls else 0.0,
        "worst_bounce_krw": min(pnls) if pnls else 0.0,
        "tp_count": sum(1 for pnl in pnls if pnl > 0.0),
        "sl_count": sum(1 for pnl in pnls if pnl < 0.0),
        "time_stop_count": 0,
    }


def _case_rows(journal: list[dict[str, Any]], *, best: bool) -> list[dict[str, Any]]:
    entries = [row for row in journal if row.get("bounce_entry")]
    entries = sorted(entries, key=lambda row: float(row.get("pnl_krw", 0.0)), reverse=best)[:10]
    return [_case(row) for row in entries]


def _missed_bounce_rows(journal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [row for row in journal if row.get("bear_bounce_candidate") and not row.get("bounce_entry") and float(row.get("pnl_krw", 0.0)) > 0.0]
    return [_case(row) for row in sorted(rows, key=lambda row: float(row.get("pnl_krw", 0.0)), reverse=True)[:10]]


def _false_bounce_rows(journal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [row for row in journal if row.get("bounce_entry") and float(row.get("pnl_krw", 0.0)) < 0.0]
    return [_case(row) for row in sorted(rows, key=lambda row: float(row.get("pnl_krw", 0.0)))[:10]]


def _case(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "trade_id": row.get("trade_id"),
        "date": row.get("date"),
        "market": row.get("market"),
        "market_state": row.get("market_state"),
        "plan": row.get("plan"),
        "setup_type": row.get("setup_type"),
        "score": row.get("bear_bounce_score"),
        "pnl_krw": row.get("pnl_krw"),
        "factors": row.get("bear_bounce_factors"),
        "lookahead_check": row.get("lookahead_check"),
    }


def _guard_activation_insight(journal: list[dict[str, Any]]) -> dict[str, Any]:
    guard_rows = [row for row in journal if row.get("guard_on")]
    hard_rows = [row for row in journal if row.get("hard_guard")]
    return {
        "guard_on_count": len(guard_rows),
        "hard_guard_count": len(hard_rows),
        "guard_on_pnl_krw": sum(float(row.get("pnl_krw", 0.0)) for row in guard_rows),
        "hard_guard_pnl_krw": sum(float(row.get("pnl_krw", 0.0)) for row in hard_rows),
        "non_plan_a_guard_count": sum(1 for row in guard_rows if row.get("plan") != "PLAN_A_ICT_FAT_TAIL"),
        "plan_a_guard_count": sum(1 for row in guard_rows if row.get("plan") == "PLAN_A_ICT_FAT_TAIL"),
        "dominance_risk_guard_count": sum(1 for row in guard_rows if row.get("market_state") in {"BTC_LED_MARKET", "RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "LOCKDOWN"}),
    }


def _scenario_decision(row: dict[str, Any], baseline: dict[str, Any]) -> str:
    better_return = float(row["return_pct"]) > float(baseline["return_pct"])
    better_mdd = float(row["mdd_pct"]) > float(baseline["mdd_pct"])
    if row["scenario"] == "ACTIVE_BASELINE":
        return "ACTIVE_PAPER_CANDIDATE"
    if better_return and better_mdd:
        return "BEAR_RESPONSE_CANDIDATE"
    if better_mdd:
        return "DEFENSE_CANDIDATE"
    return "PAPER_MORE_REQUIRED"


def _loss_guard_sensitivity_configs() -> list[dict[str, Any]]:
    configs = []
    for month in (-2.0, -3.0, -4.0):
        for pf in (0.8, 1.0, 1.2):
            for dd in (-8.0, -10.0, -12.0):
                configs.append(
                    {
                        "name": f"LG_M{abs(month):.0f}_PF{pf:.1f}_DD{abs(dd):.0f}",
                        "month_loss_threshold": month,
                        "pf_threshold": pf,
                        "dd_threshold": dd,
                        "cap": 0.35,
                        "hard_cash": True,
                        "dominance_gate": True,
                        "pf_window": 20,
                        "min_pf_trades": 20,
                    }
                )
    return configs


def _active_config(enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {
            "month_loss_threshold": -99.0,
            "pf_threshold": -1.0,
            "dd_threshold": -99.0,
            "cap": 1.0,
            "hard_cash": False,
            "dominance_gate": False,
            "pf_window": 20,
            "min_pf_trades": 20,
        }
    return {
        "month_loss_threshold": -3.0,
        "pf_threshold": 1.0,
        "dd_threshold": -10.0,
        "cap": 0.35,
        "hard_cash": True,
        "dominance_gate": True,
        "pf_window": 20,
        "min_pf_trades": 20,
    }
