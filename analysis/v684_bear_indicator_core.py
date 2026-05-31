from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from analysis.v681_compounding_control_tower import _load_contexts
from analysis.v682_bear_response_analyzer import _active_config, _simulate
from analysis.v683_paper_runtime_analyzer import _simulate_route
from bear_validation.bear_bounce_v3_score import score_bear_bounce_v3
from bear_validation.bear_router_v684 import route_for_state
from bear_validation.bear_window_detector import detect_bear_windows
from bear_validation.indicator_effectiveness_analyzer import indicator_rows
from bear_validation.metrics import hwm_giveback, period_rows, saved_loss_vs, summary_from_journal
from bear_validation.risk_sizing_models import apply_sizing_model
from paper_runtime.live_order_guard import assert_live_orders_disabled
from paper_runtime.paper_runtime_schema import safety_flags


ACTIVE_ROUTE = "LG_V2_BALANCED_PLUS_DOM_GATE"
SHADOW_ROUTES = ["LG_M3_PF0.8_DD8", "LOSS_GUARD_2026_ROUTER_V1_SHADOW", "BASE_BALANCED", "BASE_ROLLING"]


def load_v684_contexts(reports_dir: str | Path = "docs/reports") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return _load_contexts(str(reports_dir), "replay_store/historical_archive", "data/processed")


def active_journal(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports", start_date: str = "2022-01-01") -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    contexts, quality = load_v684_contexts(reports_dir)
    contexts = [ctx for ctx in contexts if str(ctx["trade"].get("entry_time", ""))[:10] >= start_date]
    journal = _enrich(_simulate_route(ACTIVE_ROUTE, contexts, initial_cash_krw)["journal"], contexts)
    return journal, contexts, quality


def build_bear_windows_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    journal, _, quality = active_journal(initial_cash_krw, reports_dir)
    windows = detect_bear_windows(journal)
    return {
        "schema_version": "v684_bear_windows_v1",
        "active_route": ACTIVE_ROUTE,
        "initial_cash_krw": initial_cash_krw,
        "windows": windows,
        "window_count": len(windows),
        "stress_months": ["2025-02", "2025-08", "2025-09", "2025-11", "2026-02"],
        "dominance_data_quality": quality,
        "decision": "BEAR_WINDOWS_READY" if windows else "PAPER_MORE_REQUIRED",
        **safety_flags(),
    }


def build_indicator_effectiveness_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    journal, _, quality = active_journal(initial_cash_krw, reports_dir)
    rows = indicator_rows(journal)
    return {
        "schema_version": "v684_indicator_effectiveness_v1",
        "active_route": ACTIVE_ROUTE,
        "initial_cash_krw": initial_cash_krw,
        "indicators": rows,
        "candidate_indicators": [row["indicator"] for row in rows if row["decision"] == "INDICATOR_CANDIDATE"],
        "dominance_data_quality": quality,
        "decision": "INDICATOR_VALIDATION_READY",
        **safety_flags(),
    }


def build_loss_guard_indicator_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    journal, contexts, quality = active_journal(initial_cash_krw, reports_dir)
    baseline = _enrich(_simulate("ACTIVE_BASELINE", contexts, initial_cash_krw, loss_guard_config=_active_config(False))["journal"], contexts)
    scenarios: dict[str, list[dict[str, Any]]] = {
        "LG_BASE": journal,
        "LG_DOMINANCE_RISK_GATE": _rescale(journal, initial_cash_krw, lambda row: 0.35 if _dominance_risk(row) else 1.0),
        "LG_200MA_BEAR_REGIME": _rescale(journal, initial_cash_krw, lambda row: 0.35 if _ma_bear(row) else 1.0),
        "LG_VOLATILITY_TARGETING": apply_sizing_model("VOLATILITY_TARGETING", journal, initial_cash_krw)["journal"],
        "LG_ATR_STOP": apply_sizing_model("ATR_TRAILING_STOP", journal, initial_cash_krw)["journal"],
        "LG_VWAP_FAILURE": _rescale(journal, initial_cash_krw, lambda row: 0.35 if str(row.get("market_state")) in {"EDGE_DECAY", "RISK_OFF_ALT_WEAK"} else 1.0),
        "LG_HMM_RISK_OFF": _rescale(journal, initial_cash_krw, lambda row: 0.35 if str(row.get("market_state")) in {"RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "LOCKDOWN"} else 1.0),
        "LG_COMBINED_GUARD": _rescale(journal, initial_cash_krw, lambda row: 0.25 if _combined_guard(row) else 1.0),
    }
    rows = []
    base_summary = summary_from_journal("LG_BASE", journal, initial_cash_krw)
    for name, candidate in scenarios.items():
        row = summary_from_journal(name, candidate, initial_cash_krw)
        row.update(saved_loss_vs(candidate, baseline))
        row["decision"] = _candidate_decision(row, base_summary)
        if name == "LG_ATR_STOP":
            row["decision"] = "ATR_RESEARCH_ONLY_PRICE_PATH_REQUIRED"
        rows.append(row)
    return {
        "schema_version": "v684_loss_guard_indicator_lab_v1",
        "baseline_reference": "ACTIVE_BASELINE_WITHOUT_LG",
        "active_route": ACTIVE_ROUTE,
        "initial_cash_krw": initial_cash_krw,
        "scenarios": rows,
        "dominance_data_quality": quality,
        "decision": "BEAR_ROUTER_CANDIDATE" if any(row["decision"].endswith("CANDIDATE") for row in rows) else "PAPER_MORE_REQUIRED",
        **safety_flags(),
    }


def build_bear_bounce_v3_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    active, contexts, quality = active_journal(initial_cash_krw, reports_dir)
    journal = _bounce_v3_journal(active, contexts, initial_cash_krw)
    summary = summary_from_journal("BEAR_BOUNCE_V3_RESEARCH", journal, initial_cash_krw)
    type_rows = _bounce_type_rows(journal)
    summary["bounce_candidates"] = sum(row["candidates"] for row in type_rows)
    summary["bounce_entries"] = sum(row["entries"] for row in type_rows)
    summary["decision"] = "BEAR_BOUNCE_RESEARCH_READY" if summary["bounce_entries"] else "PAPER_MORE_REQUIRED"
    return {
        "schema_version": "v684_bear_bounce_v3_v1",
        "active_applied": False,
        "initial_cash_krw": initial_cash_krw,
        "scenario": summary,
        "bounce_types": type_rows,
        "best_cases": _case_rows(journal, True),
        "worst_cases": _case_rows(journal, False),
        "dominance_data_quality": quality,
        "decision": summary["decision"],
        **safety_flags(),
    }


def build_risk_sizing_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    journal, _, quality = active_journal(initial_cash_krw, reports_dir)
    names = ["FIXED_MULTIPLIER", "VOLATILITY_TARGETING", "ATR_POSITION_SIZING", "ATR_TRAILING_STOP", "FRACTIONAL_KELLY_0.1"]
    base = summary_from_journal("FIXED_MULTIPLIER", journal, initial_cash_krw)
    rows = []
    for name in names:
        result = {"summary": base, "journal": journal} if name == "FIXED_MULTIPLIER" else apply_sizing_model(name, journal, initial_cash_krw)
        row = dict(result["summary"])
        row.update(hwm_giveback(result["journal"], initial_cash_krw))
        row["decision"] = _candidate_decision(row, base, defense_only=True)
        if name == "ATR_TRAILING_STOP":
            row["decision"] = "ATR_RESEARCH_ONLY_PRICE_PATH_REQUIRED"
        rows.append(row)
    return {
        "schema_version": "v684_risk_sizing_lab_v1",
        "active_applied": False,
        "initial_cash_krw": initial_cash_krw,
        "models": rows,
        "dominance_data_quality": quality,
        "decision": "INDICATOR_VALIDATION_READY",
        **safety_flags(),
    }


def build_bear_router_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    active, _, quality = active_journal(initial_cash_krw, reports_dir)
    routed = _router_journal(active, initial_cash_krw)
    active_row = summary_from_journal(ACTIVE_ROUTE, active, initial_cash_krw)
    router_row = summary_from_journal("BEAR_ROUTER_V684_SHADOW", routed, initial_cash_krw)
    for row, journal in ((active_row, active), (router_row, routed)):
        row.update(hwm_giveback(journal, initial_cash_krw))
        years = {item["period"]: item for item in period_rows(journal, "year")}
        row["return_2025_pct"] = years.get("2025", {}).get("return_pct", 0.0)
        row["return_2026_pct"] = years.get("2026", {}).get("return_pct", 0.0)
        row["decision"] = _candidate_decision(row, active_row)
    return {
        "schema_version": "v684_bear_router_v1",
        "active_route": ACTIVE_ROUTE,
        "active_route_change_applied": False,
        "manual_approval_required": True,
        "scenarios": [active_row, router_row],
        "route_usage_count": dict(Counter(row.get("selected_route") for row in routed)),
        "routing_rules": _routing_rules(),
        "dominance_data_quality": quality,
        "decision": "BEAR_ROUTER_CANDIDATE" if router_row["decision"].endswith("CANDIDATE") else "PAPER_MORE_REQUIRED",
        **safety_flags(),
    }


def write_payload(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _enrich(journal: list[dict[str, Any]], contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row, ctx in zip(journal, contexts):
        state = ctx.get("state", {})
        new = dict(row)
        new.setdefault("btc_trend", state.get("btc_trend"))
        new.setdefault("dominance_regime", state.get("dominance_regime"))
        new.setdefault("market_state", state.get("market_state"))
        out.append(new)
    return out


def _rescale(journal: list[dict[str, Any]], initial_cash_krw: float, factor_fn: Callable[[dict[str, Any]], float]) -> list[dict[str, Any]]:
    equity = initial_cash_krw
    peak = initial_cash_krw
    out = []
    for row in journal:
        before = equity
        factor = factor_fn(row)
        pnl = float(row.get("pnl_krw", 0.0)) * factor
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        new = dict(row)
        new.update(
            {
                "equity_before": before,
                "equity_after": equity,
                "pnl_krw": pnl,
                "drawdown_pct": (equity / peak - 1.0) * 100.0 if peak else 0.0,
                "risk_multiplier_after_defense": float(row.get("risk_multiplier_after_defense", 1.0)) * factor,
            }
        )
        if factor == 0.0:
            new["defense_action"] = "SKIP"
        out.append(new)
    return out


def _dominance_risk(row: dict[str, Any]) -> bool:
    return str(row.get("market_state")) in {"BTC_LED_MARKET", "RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "LOCKDOWN"} or "SPIKE" in str(row.get("dominance_regime"))


def _ma_bear(row: dict[str, Any]) -> bool:
    return str(row.get("btc_trend")) == "DOWN" or str(row.get("market_state")) in {"BEAR_DEFENSE", "LOCKDOWN"}


def _combined_guard(row: dict[str, Any]) -> bool:
    flags = [bool(row.get("guard_on")), _dominance_risk(row), _ma_bear(row), str(row.get("market_state")) in {"RISK_OFF_ALT_WEAK", "LOCKDOWN"}]
    return sum(1 for flag in flags if flag) >= 2


def _candidate_decision(row: dict[str, Any], base: dict[str, Any], defense_only: bool = False) -> str:
    better_mdd = float(row.get("mdd_pct", -999.0)) > float(base.get("mdd_pct", -999.0))
    better_return = float(row.get("return_pct", -999.0)) >= float(base.get("return_pct", -999.0))
    if row.get("scenario") == base.get("scenario"):
        return "BASELINE"
    if better_mdd and (better_return or defense_only):
        return "BEAR_ROUTER_CANDIDATE"
    if better_mdd:
        return "SHADOW_DEFENSE_CANDIDATE"
    return "PAPER_MORE_REQUIRED"


def _bounce_v3_journal(active: list[dict[str, Any]], contexts: list[dict[str, Any]], initial_cash_krw: float) -> list[dict[str, Any]]:
    equity = initial_cash_krw
    peak = initial_cash_krw
    out = []
    for active_row, ctx in zip(active, contexts):
        score = score_bear_bounce_v3(ctx, active_row)
        before = equity
        entered = bool(score["bear_bounce_v3_candidate"])
        mult = 0.35 if score["bear_bounce_v3_high_confidence"] else 0.25 if entered else 0.0
        raw = float(ctx.get("trade", {}).get("pnl_krw", active_row.get("pnl_krw", 0.0))) * mult
        pnl = max(raw, -before * 0.015 * max(mult, 0.25)) if entered else 0.0
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        new = dict(active_row)
        new.update(score)
        new.update(
            {
                "scenario": "BEAR_BOUNCE_V3_RESEARCH",
                "defense_action": "ENTER" if entered else "SKIP",
                "bounce_entry": entered,
                "bounce_type": _bounce_type(score),
                "risk_multiplier_after_defense": mult,
                "equity_before": before,
                "equity_after": equity,
                "pnl_krw": pnl,
                "drawdown_pct": (equity / peak - 1.0) * 100.0 if peak else 0.0,
            }
        )
        out.append(new)
    return out


def _bounce_type(row: dict[str, Any]) -> str:
    factors = set(row.get("bear_bounce_v3_factors", []))
    if "SWEEP_OR_REVERSAL" in factors:
        return "SUPPORT_CONFLUENCE_BOUNCE"
    if "PLAN_A_STRUCTURE" in factors:
        return "30M_IMPULSE_50_HOLD"
    if "BTC_DROP_EASING_PROXY" in factors:
        return "VWAP_BOUNCE_PROXY"
    return "RSI_BOLLINGER_BOUNCE_PROXY"


def _bounce_type_rows(journal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        groups[str(row.get("bounce_type", "UNKNOWN"))].append(row)
    rows = []
    for name, items in sorted(groups.items()):
        entries = [row for row in items if row.get("bounce_entry")]
        pnls = [float(row.get("pnl_krw", 0.0)) for row in entries]
        rows.append(
            {
                "bounce_type": name,
                "candidates": sum(1 for row in items if row.get("bear_bounce_v3_candidate")),
                "entries": len(entries),
                "win_rate": sum(1 for pnl in pnls if pnl > 0.0) / len(pnls) * 100.0 if pnls else 0.0,
                "net_pnl": sum(pnls),
                "avg_hold": "30m-4h proxy",
                "TP": sum(1 for pnl in pnls if pnl > 0.0),
                "SL": sum(1 for pnl in pnls if pnl < 0.0),
                "decision": "BEAR_BOUNCE_RESEARCH_READY" if sum(pnls) > 0 and len(entries) >= 3 else "RESEARCH_ONLY",
            }
        )
    return rows


def _case_rows(journal: list[dict[str, Any]], best: bool) -> list[dict[str, Any]]:
    entries = [row for row in journal if row.get("bounce_entry")]
    rows = sorted(entries, key=lambda row: float(row.get("pnl_krw", 0.0)), reverse=best)[:10]
    return [
        {
            "trade_id": row.get("trade_id"),
            "date": row.get("date"),
            "market": row.get("market"),
            "bounce_type": row.get("bounce_type"),
            "score": row.get("bear_bounce_v3_score"),
            "pnl_krw": row.get("pnl_krw"),
            "factors": row.get("bear_bounce_v3_factors"),
            "lookahead_check": row.get("lookahead_check"),
        }
        for row in rows
    ]


def _router_journal(active: list[dict[str, Any]], initial_cash_krw: float) -> list[dict[str, Any]]:
    equity = initial_cash_krw
    peak = initial_cash_krw
    out = []
    for row in active:
        decision = route_for_state(row)
        before = equity
        cap = float(decision["cap"])
        pnl = float(row.get("pnl_krw", 0.0)) * cap
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        new = dict(row)
        new.update(
            {
                "scenario": "BEAR_ROUTER_V684_SHADOW",
                "selected_route": decision["route"],
                "risk_multiplier_after_defense": float(row.get("risk_multiplier_after_defense", 1.0)) * cap,
                "defense_action": "SKIP" if cap <= 0.0 else row.get("defense_action", "ENTER"),
                "equity_before": before,
                "equity_after": equity,
                "pnl_krw": pnl,
                "drawdown_pct": (equity / peak - 1.0) * 100.0 if peak else 0.0,
            }
        )
        out.append(new)
    return out


def _routing_rules() -> list[dict[str, Any]]:
    states = ["BULL_ATTACK", "ALT_FRIENDLY", "NORMAL", "BTC_LED_MARKET", "EDGE_DECAY", "RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "BEAR_BOUNCE_ONLY", "LOCKDOWN"]
    return [route_for_state({"market_state": state}) for state in states]
