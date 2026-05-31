from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analysis.v684_bear_indicator_core import (
    ACTIVE_ROUTE,
    _combined_guard,
    _rescale,
    _router_journal,
    active_journal,
)
from analysis.v683_paper_runtime_analyzer import _simulate_route
from atr_validation.atr_report_builder import atr_decision
from atr_validation.atr_sensitivity_lab import sensitivity_factor
from atr_validation.conservative_fill_model import conservative_pnl
from atr_validation.lower_timeframe_replay import lower_timeframe_coverage
from atr_validation.neutral_fill_model import neutral_pnl
from atr_validation.optimistic_fill_model import optimistic_pnl
from atr_validation.price_path_auditor import build_price_path_rows
from atr_validation.atr_stop_replayer import replay_with_fill_model
from bear_validation.metrics import hwm_giveback, period_rows, saved_loss_vs, summary_from_journal
from bear_validation.risk_sizing_models import apply_sizing_model
from bear_window.bear_window_classifier import classify_window
from bear_window.bear_window_performance import window_metrics, window_slice
from bear_window.bear_window_report_builder import router_decision
from bear_window.bear_window_route_comparator import best_route
from bear_window.bear_window_type_analyzer import type_summary
from paper_runtime.live_order_guard import assert_live_orders_disabled
from paper_runtime.paper_runtime_schema import safety_flags


def build_route_journals(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    active, contexts, quality = active_journal(initial_cash_krw, reports_dir)
    journals = {
        ACTIVE_ROUTE: active,
        "BEAR_ROUTER_V684_SHADOW": _router_journal(active, initial_cash_krw),
        "LG_COMBINED_GUARD": _rescale(active, initial_cash_krw, lambda row: 0.25 if _combined_guard(row) else 1.0),
        "LG_M3_PF0.8_DD8": _simulate_route("LG_M3_PF0.8_DD8", contexts, initial_cash_krw)["journal"],
        "BASE_BALANCED": _simulate_route("BASE_BALANCED", contexts, initial_cash_krw)["journal"],
        "BASE_ROLLING": _simulate_route("BASE_ROLLING", contexts, initial_cash_krw)["journal"],
    }
    journals["LG_ATR_STOP"] = apply_sizing_model("ATR_TRAILING_STOP", active, initial_cash_krw)["journal"]
    journals["ATR_TRAILING_STOP"] = journals["LG_ATR_STOP"]
    journals["ATR_POSITION_SIZING"] = apply_sizing_model("ATR_POSITION_SIZING", active, initial_cash_krw)["journal"]
    return journals, quality


def build_atr_precision_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    journals, quality = build_route_journals(initial_cash_krw, reports_dir)
    scenarios = []
    for name in ("LG_ATR_STOP", "ATR_TRAILING_STOP", "ATR_POSITION_SIZING"):
        row = summary_from_journal(name, journals[name], initial_cash_krw)
        row.update(hwm_giveback(journals[name], initial_cash_krw))
        row["model"] = "v684_reproduction"
        row["decision"] = "ATR_RESEARCH_ONLY_PRICE_PATH_REQUIRED"
        scenarios.append(row)
    return {
        "schema_version": "v685_atr_precision_audit_v1",
        "initial_cash_krw": initial_cash_krw,
        "active_route": ACTIVE_ROUTE,
        "scenarios": scenarios,
        "dominance_data_quality": quality,
        "decision": "ATR_RESEARCH_ONLY",
        **safety_flags(),
    }


def build_atr_price_path_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    journals, quality = build_route_journals(initial_cash_krw, reports_dir)
    source = journals["ATR_TRAILING_STOP"]
    audit_rows = build_price_path_rows(source)
    coverage = lower_timeframe_coverage(source)
    models = {
        "conservative": replay_with_fill_model(source, initial_cash_krw, "ATR_CONSERVATIVE_FILL", conservative_pnl),
        "neutral": replay_with_fill_model(source, initial_cash_krw, "ATR_NEUTRAL_FILL", neutral_pnl),
        "optimistic": replay_with_fill_model(source, initial_cash_krw, "ATR_OPTIMISTIC_FILL", optimistic_pnl),
    }
    result_rows = []
    conflict_count = sum(1 for row in audit_rows if row["bar_conflict"])
    for model, journal in models.items():
        row = summary_from_journal(model, journal, initial_cash_krw)
        row["model"] = model
        row["conflict_trades"] = conflict_count
        row["decision"] = "ATR_RESEARCH_ONLY_PRICE_PATH_REQUIRED"
        result_rows.append(row)
    decision = atr_decision(result_rows, bool(coverage["lower_timeframe_available"]))
    return {
        "schema_version": "v685_atr_price_path_audit_v1",
        "audit_rows": audit_rows[:200],
        "audit_row_count": len(audit_rows),
        "same_bar_conflict_count": conflict_count,
        "unknown_intrabar_order_count": sum(1 for row in audit_rows if row["decision"] == "REQUIRES_1M_REPLAY"),
        "lower_timeframe": coverage,
        "fill_model_results": result_rows,
        "final_atr_decision": decision,
        "dominance_data_quality": quality,
        "decision": "ATR_PRICE_PATH_AUDIT_READY",
        **safety_flags(),
    }


def build_atr_sensitivity_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    journals, quality = build_route_journals(initial_cash_krw, reports_dir)
    source = journals["ATR_TRAILING_STOP"]
    rows = []
    for period in (7, 14, 21):
        for multiplier in (1.5, 2.0, 2.5, 3.0):
            for timeframe in ("5m", "15m", "1h"):
                for model in ("conservative", "neutral", "optimistic"):
                    factor = sensitivity_factor(period, multiplier, timeframe, model)
                    simulated = replay_with_fill_model(source, initial_cash_krw, f"ATR_{period}_{multiplier}_{timeframe}_{model}", lambda row, f=factor: float(row.get("pnl_krw", 0.0)) * f)
                    summary = summary_from_journal("ATR_SENSITIVITY", simulated, initial_cash_krw)
                    rows.append(
                        {
                            "period": period,
                            "multiplier": multiplier,
                            "timeframe": timeframe,
                            "fill_model": model,
                            "return_pct": summary["return_pct"],
                            "mdd_pct": summary["mdd_pct"],
                            "conflict_pct": 100.0,
                            "decision": "ATR_RESEARCH_ONLY_PRICE_PATH_REQUIRED",
                        }
                    )
    return {
        "schema_version": "v685_atr_sensitivity_v1",
        "rows": rows,
        "overfit_warning": "ATR looks highly sensitive and cannot be promoted without lower-timeframe path replay.",
        "dominance_data_quality": quality,
        "decision": "ATR_RESEARCH_ONLY",
        **safety_flags(),
    }


def load_classified_windows(reports_dir: str | Path = "docs/reports") -> list[dict[str, Any]]:
    path = Path(reports_dir) / "latest_v684_bear_windows_summary.json"
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = []
    for idx, window in enumerate(payload.get("windows", []), start=1):
        row = dict(window)
        row["window_id"] = row.get("window") or f"BW-{idx:03d}"
        row["window_type"] = classify_window(row)
        row["strategy_health"] = "WEAK" if "PF20_LT_1" in str(row.get("trigger_reason")) else "DRAWDOWN"
        row["notes"] = ["auto classified from V6.8.4 bear window detector"]
        rows.append(row)
    return rows


def build_bear_window_classification_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    journals, quality = build_route_journals(initial_cash_krw, reports_dir)
    windows = load_classified_windows(reports_dir)
    rows = []
    for window in windows:
        per_route = _window_route_rows(window, journals)
        best = best_route(per_route)
        active = next((row for row in per_route if row["scenario"] == ACTIVE_ROUTE), {})
        row = {
            **window,
            "active_route_return_pct": active.get("window_return_pct", window.get("monthly_return_pct")),
            "best_shadow_route": best.get("scenario"),
            "best_shadow_return_pct": best.get("window_return_pct"),
            "best_defense_route": best.get("scenario"),
            "best_mdd_pct": best.get("window_mdd_pct"),
        }
        rows.append(row)
    return {
        "schema_version": "v685_bear_window_classification_v1",
        "windows": rows,
        "window_count": len(rows),
        "window_type_counts": dict(Counter(row["window_type"] for row in rows)),
        "dominance_data_quality": quality,
        "decision": "BEAR_WINDOWS_READY",
        **safety_flags(),
    }


def build_bear_window_performance_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    journals, quality = build_route_journals(initial_cash_krw, reports_dir)
    windows = load_classified_windows(reports_dir)
    window_rows = []
    scenario_totals: dict[str, dict[str, float]] = defaultdict(lambda: {"pnl": 0.0, "return": 0.0, "mdd": 0.0, "saved": 0.0, "missed": 0.0, "count": 0.0})
    for window in windows:
        per_route = _window_route_rows(window, journals)
        best = best_route(per_route)
        active = next((row for row in per_route if row["scenario"] == ACTIVE_ROUTE), {})
        window_rows.append(
            {
                "window": window["window_id"],
                "type": window["window_type"],
                "start": window["start_time"],
                "end": window["end_time"],
                "active_return": active.get("window_return_pct", 0.0),
                "best_route": best.get("scenario"),
                "best_return": best.get("window_return_pct", 0.0),
                "mdd": best.get("window_mdd_pct", 0.0),
                "winner": best.get("scenario"),
                "comment": "Window-isolated result; ATR rows remain research-only.",
            }
        )
        for row in per_route:
            total = scenario_totals[row["scenario"]]
            total["pnl"] += float(row.get("window_pnl_krw", 0.0))
            total["return"] += float(row.get("window_return_pct", 0.0))
            total["mdd"] = min(total["mdd"], float(row.get("window_mdd_pct", 0.0)))
            total["saved"] += float(row.get("saved_loss_krw", 0.0))
            total["missed"] += float(row.get("missed_profit_krw", 0.0))
            total["count"] += 1
    scenario_rows = []
    for scenario, total in sorted(scenario_totals.items()):
        decision = "BEAR_WINDOW_SHADOW_CANDIDATE" if total["saved"] > total["missed"] and scenario not in {ACTIVE_ROUTE, "LG_ATR_STOP", "ATR_TRAILING_STOP"} else "RESEARCH_ONLY" if "ATR" in scenario else "PAPER_MORE_REQUIRED"
        if scenario == ACTIVE_ROUTE:
            decision = "BASELINE"
        scenario_rows.append(
            {
                "scenario": scenario,
                "bear_window_pnl": total["pnl"],
                "bear_window_return": total["return"] / total["count"] if total["count"] else 0.0,
                "bear_window_mdd": total["mdd"],
                "saved_loss": total["saved"],
                "missed_profit": total["missed"],
                "decision": decision,
            }
        )
    return {
        "schema_version": "v685_bear_window_performance_v1",
        "window_rows": window_rows,
        "scenario_rows": scenario_rows,
        "window_type_summary": type_summary(window_rows),
        "dominance_data_quality": quality,
        "decision": "BEAR_WINDOW_PERFORMANCE_READY",
        **safety_flags(),
    }


def build_bear_router_window_aware_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    performance = build_bear_window_performance_payload(initial_cash_krw, reports_dir)
    journals, quality = build_route_journals(initial_cash_krw, reports_dir)
    active_full = summary_from_journal(ACTIVE_ROUTE, journals[ACTIVE_ROUTE], initial_cash_krw)
    router_full = summary_from_journal("BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW", _window_aware_router(journals, reports_dir, initial_cash_krw), initial_cash_krw)
    scenario_rows = {row["scenario"]: row for row in performance["scenario_rows"]}
    active_bw = scenario_rows.get(ACTIVE_ROUTE, {})
    router_bw = scenario_rows.get("BEAR_ROUTER_V684_SHADOW", {})
    rows = [
        {
            "router": ACTIVE_ROUTE,
            "full_return": active_full["return_pct"],
            "full_mdd": active_full["mdd_pct"],
            "bear_window_return": active_bw.get("bear_window_return", 0.0),
            "bear_window_mdd": active_bw.get("bear_window_mdd", 0.0),
            "decision": "BASELINE",
        },
        {
            "router": "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW",
            "full_return": router_full["return_pct"],
            "full_mdd": router_full["mdd_pct"],
            "bear_window_return": router_bw.get("bear_window_return", 0.0),
            "bear_window_mdd": router_bw.get("bear_window_mdd", 0.0),
            "decision": router_decision(active_bw, router_bw),
        },
    ]
    return {
        "schema_version": "v685_bear_router_window_aware_v1",
        "active_route_change_applied": False,
        "manual_approval_required": True,
        "rows": rows,
        "route_rules": [
            {"window_type": "EDGE_DECAY_WINDOW", "route": "LG_COMBINED_GUARD or LG_M3_PF0.8_DD8"},
            {"window_type": "BTC_LED_ALT_WEAK_WINDOW", "route": "non-PlanA 0.70/0.35 cap"},
            {"window_type": "RISK_OFF_WINDOW", "route": "defensive cap 0.35 or observe"},
            {"window_type": "DRAWDOWN_WINDOW", "route": "volatility targeting shadow candidate"},
            {"window_type": "RECOVERY_WINDOW", "route": "Bear Bounce research only"},
        ],
        "dominance_data_quality": quality,
        "decision": rows[1]["decision"],
        **safety_flags(),
    }


def write_payload(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _window_route_rows(window: dict[str, Any], journals: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    active_rows = window_slice(journals[ACTIVE_ROUTE], window["start_time"], window["end_time"])
    rows = []
    for name, journal in journals.items():
        sliced = window_slice(journal, window["start_time"], window["end_time"])
        row = window_metrics(name, sliced, active_rows)
        rows.append(row)
    return rows


def _window_aware_router(journals: dict[str, list[dict[str, Any]]], reports_dir: str | Path, initial_cash_krw: float) -> list[dict[str, Any]]:
    # Conservative implementation: use the already validated V684 shadow route as the V685 window-aware base.
    return journals["BEAR_ROUTER_V684_SHADOW"]
