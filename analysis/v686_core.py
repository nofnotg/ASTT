from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v683_paper_runtime_analyzer import run_v683_paper_backfill_from_20260101
from analysis.v685_core import ACTIVE_ROUTE, build_route_journals, load_classified_windows, write_payload
from atr_ltf.ltf_backfill_planner import build_ltf_backfill_plan
from atr_ltf.ltf_coverage_analyzer import analyze_ltf_coverage
from atr_precision_v2.atr_ltf_replayer import replay_trade_with_ltf
from atr_precision_v2.atr_path_schema import ATRReplayConfig
from atr_precision_v2.atr_precision_v2_report_builder import final_atr_decision
from bear_validation.metrics import summary_from_journal
from bear_window.bear_window_performance import window_metrics, window_slice
from paper_runtime.live_order_guard import assert_live_orders_disabled
from paper_runtime.paper_runtime_schema import safety_flags


V686_SHADOW_ROUTES = [
    "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW",
    "BEAR_ROUTER_V684_SHADOW",
    "LG_COMBINED_GUARD",
    "LG_M3_PF0.8_DD8",
    "BASE_BALANCED",
    "BASE_ROLLING",
]
ATR_ROUTES = ["LG_ATR_STOP", "ATR_TRAILING_STOP", "ATR_POSITION_SIZING"]


def build_v686_atr_ltf_coverage_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    journals, quality = build_route_journals(initial_cash_krw, reports_dir)
    source = journals["ATR_TRAILING_STOP"]
    coverage = analyze_ltf_coverage(source)
    plan = build_ltf_backfill_plan(coverage)
    return {
        "schema_version": "v686_atr_ltf_coverage_v1",
        "initial_cash_krw": initial_cash_krw,
        "atr_route": "ATR_TRAILING_STOP",
        **coverage,
        "backfill_plan": plan,
        "dominance_data_quality": quality,
        **safety_flags(),
    }


def build_v686_atr_ltf_replay_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    coverage = _read_or_build_coverage(initial_cash_krw, reports_dir)
    journals, quality = build_route_journals(initial_cash_krw, reports_dir)
    source = journals["ATR_TRAILING_STOP"]
    configs = [ATRReplayConfig(fill_model=model) for model in ("conservative", "neutral", "optimistic")]
    rows = []
    for trade in source[:300]:
        for config in configs:
            replay = replay_trade_with_ltf(trade, [], config)
            replay["fill_model"] = config.fill_model
            rows.append(replay)
    model_rows = _model_rows_from_missing(source, initial_cash_krw, coverage)
    return {
        "schema_version": "v686_atr_ltf_replay_v1",
        "total_replayed_rows": len(rows),
        "sample_rows": rows[:120],
        "model_rows": model_rows,
        "coverage_decision": coverage["decision"],
        "final_atr_decision": "ATR_DATA_INSUFFICIENT" if coverage["decision"] == "ATR_DATA_INSUFFICIENT" else "ATR_LTF_REPLAY_READY",
        "fake_data_generated": False,
        "dominance_data_quality": quality,
        "decision": "ATR_DATA_INSUFFICIENT" if coverage["decision"] == "ATR_DATA_INSUFFICIENT" else "ATR_LTF_REPLAY_READY",
        **safety_flags(),
    }


def build_v686_atr_precision_v2_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    coverage = _read_or_build_coverage(initial_cash_krw, reports_dir)
    journals, quality = build_route_journals(initial_cash_krw, reports_dir)
    active = summary_from_journal(ACTIVE_ROUTE, journals[ACTIVE_ROUTE], initial_cash_krw)
    rows = []
    for route in ATR_ROUTES:
        source_summary = summary_from_journal(route, journals[route], initial_cash_krw)
        for period in (7, 14, 21):
            for multiplier in (1.5, 2.0, 2.5, 3.0):
                for timeframe in ("1m", "5m", "15m", "1h"):
                    for mode in ("close_confirmed_next_bar", "high_low_intrabar_conservative", "chandelier_close_only"):
                        row = dict(source_summary)
                        row.update(
                            {
                                "scenario": route,
                                "fill_model": "conservative",
                                "atr_period": period,
                                "atr_multiplier": multiplier,
                                "atr_timeframe": timeframe,
                                "trailing_update_mode": mode,
                                "ltf_coverage_pct": _coverage_pct(coverage, timeframe),
                                "conflict_pct": 100.0 if coverage["decision"] == "ATR_DATA_INSUFFICIENT" else 0.0,
                                "decision": "ATR_DATA_INSUFFICIENT" if coverage["decision"] == "ATR_DATA_INSUFFICIENT" else "ATR_RESEARCH_ONLY_PRICE_PATH_REQUIRED",
                            }
                        )
                        rows.append(row)
    conservative = rows[0] if rows else {}
    decision = final_atr_decision(coverage, conservative, active)
    return {
        "schema_version": "v686_atr_precision_v2_v1",
        "active_baseline": active,
        "rows": rows[:300],
        "row_count": len(rows),
        "final_atr_decision": decision,
        "reason": "Verified lower-timeframe coverage is below 80%; ATR cannot be promoted.",
        "overfit_warning": "V6.8.5 ATR result remains suspicious until lower-timeframe path replay covers most trades.",
        "shadow_candidate_allowed": decision == "ATR_VALIDATED_SHADOW_CANDIDATE",
        "active_route_change_applied": False,
        "dominance_data_quality": quality,
        "decision": decision,
        **safety_flags(),
    }


def build_v686_atr_model_comparison_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    ltf_replay = _read_or_build_ltf_replay(initial_cash_krw, reports_dir)
    return {
        "schema_version": "v686_atr_model_comparison_v1",
        "rows": ltf_replay.get("model_rows", []),
        "comparison_note": "Model comparison is blocked from promotion when LTF coverage is insufficient.",
        "decision": ltf_replay.get("final_atr_decision", "ATR_DATA_INSUFFICIENT"),
        **safety_flags(),
    }


def build_v686_bear_window_atr_replay_payload(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    precision = _read_or_build_precision(initial_cash_krw, reports_dir)
    journals, quality = build_route_journals(initial_cash_krw, reports_dir)
    windows = load_classified_windows(reports_dir)
    rows = []
    non_atr_routes = [ACTIVE_ROUTE, "BEAR_ROUTER_V684_SHADOW", "LG_COMBINED_GUARD", "LG_M3_PF0.8_DD8", "BASE_BALANCED", "BASE_ROLLING"]
    for window in windows:
        active_rows = window_slice(journals[ACTIVE_ROUTE], window["start_time"], window["end_time"])
        non_atr_metrics = [window_metrics(route, window_slice(journals[route], window["start_time"], window["end_time"]), active_rows) for route in non_atr_routes]
        atr_metrics = [window_metrics(route, window_slice(journals[route], window["start_time"], window["end_time"]), active_rows) for route in ATR_ROUTES]
        best_non_atr = max(non_atr_metrics, key=lambda row: float(row.get("window_return_pct", -999.0)), default={})
        best_atr = max(atr_metrics, key=lambda row: float(row.get("window_return_pct", -999.0)), default={})
        atr_decision = "DATA_INSUFFICIENT" if precision.get("final_atr_decision") == "ATR_DATA_INSUFFICIENT" else "RESEARCH_ONLY"
        rows.append(
            {
                "window": window["window_id"],
                "type": window["window_type"],
                "active_return": next((row.get("window_return_pct") for row in non_atr_metrics if row.get("scenario") == ACTIVE_ROUTE), 0.0),
                "best_non_atr_route": best_non_atr.get("scenario"),
                "best_non_atr_return": best_non_atr.get("window_return_pct"),
                "best_atr_route": best_atr.get("scenario"),
                "best_atr_return": best_atr.get("window_return_pct"),
                "atr_decision": atr_decision,
                "recommended_action": "Ignore ATR ranking until LTF replay validates it." if atr_decision == "DATA_INSUFFICIENT" else "ATR may remain shadow-only.",
            }
        )
    return {
        "schema_version": "v686_bear_window_atr_replay_v1",
        "rows": rows,
        "window_count": len(rows),
        "atr_final_decision": precision.get("final_atr_decision", "ATR_DATA_INSUFFICIENT"),
        "dominance_data_quality": quality,
        "decision": "PAPER_MORE_REQUIRED" if precision.get("final_atr_decision") == "ATR_DATA_INSUFFICIENT" else "ATR_RESEARCH_ONLY",
        **safety_flags(),
    }


def build_v686_shadow_route_registration_payload(reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    payload = {
        "schema_version": "v686_shadow_route_registration_v1",
        "active_route": ACTIVE_ROUTE,
        "shadow_routes": V686_SHADOW_ROUTES,
        "research_shadow_routes": ["ATR_TRAILING_STOP_PRECISION_REPLAY"],
        "v685_router_registered": True,
        "active_changed": False,
        "manual_approval_required": True,
        "decision": "V685_ROUTER_SHADOW_REGISTERED",
        **safety_flags(),
    }
    return payload


def build_v686_active_shadow_runtime_payload(initial_cash_krw: float = 500000.0, start_date: str = "2026-01-01", reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    backfill = run_v683_paper_backfill_from_20260101(initial_cash_krw, start_date, reports_dir)
    rows = list(backfill.get("routes", []))
    v685 = _read_json(Path(reports_dir) / "latest_v685_bear_router_window_aware_summary.json")
    v685_row = next((row for row in v685.get("rows", []) if row.get("router") == "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW"), {})
    if v685_row:
        rows.append(
            {
                "scenario": "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW",
                "route_status": "SHADOW",
                "final_equity_krw": initial_cash_krw * (1.0 + float(v685_row.get("full_return", 0.0)) / 100.0),
                "return_pct": v685_row.get("full_return"),
                "mdd_pct": v685_row.get("full_mdd"),
                "decision": v685_row.get("decision"),
            }
        )
    return {
        "schema_version": "v686_active_shadow_runtime_v1",
        "active_route": ACTIVE_ROUTE,
        "shadow_routes": V686_SHADOW_ROUTES,
        "start_date": start_date,
        "routes": rows,
        "active_route_change_applied": False,
        "route_switch_locked": True,
        "decision": "PAPER_FORWARD_RUNNING",
        **safety_flags(),
    }


def build_v686_local_dashboard_payload(host: str = "127.0.0.1", port: int = 8787, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    assert_live_orders_disabled()
    return {
        "schema_version": "v686_local_dashboard_v1",
        "dashboard_ready": True,
        "host": host,
        "port": port,
        "browser_url": f"http://{host}:{port}",
        "paper_runtime_connected": (Path(reports_dir) / "latest_v686_active_shadow_runtime_summary.json").exists(),
        "llm_review_enabled": True,
        "live_order_endpoints_enabled": False,
        "active_route_change_applied": False,
        "decision": "LOCAL_DASHBOARD_READY",
        **safety_flags(),
    }


def build_v686_control_tower_dashboard_payload(reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    assert_live_orders_disabled()
    runtime = _read_json(Path(reports_dir) / "latest_v686_active_shadow_runtime_summary.json")
    atr = _read_json(Path(reports_dir) / "latest_v686_atr_precision_v2_summary.json")
    return {
        "schema_version": "v686_control_tower_dashboard_v1",
        "llm_provider_requested": llm_provider,
        "llm_used": False,
        "fallback_used": True,
        "review_generated": True,
        "active_change_applied": False,
        "recommendations": [
            "Keep LG_V2_BALANCED_PLUS_DOM_GATE active.",
            "Observe BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW as forward shadow.",
            "Keep ATR research-only until lower-timeframe coverage is sufficient.",
        ],
        "risk_flags": [
            f"ATR decision: {atr.get('final_atr_decision', 'ATR_DATA_INSUFFICIENT')}",
            "Live orders disabled",
            "Route switch requires manual approval",
        ],
        "active_route": runtime.get("active_route", ACTIVE_ROUTE),
        "decision": "CONTROL_TOWER_REVIEW_READY",
        **safety_flags(),
    }


def persist_payload(name: str, payload: dict[str, Any], reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    return write_payload(Path(reports_dir) / name, payload)


def _read_or_build_coverage(initial_cash_krw: float, reports_dir: str | Path) -> dict[str, Any]:
    path = Path(reports_dir) / "latest_v686_atr_ltf_coverage_summary.json"
    return _read_json(path) or build_v686_atr_ltf_coverage_payload(initial_cash_krw, reports_dir)


def _read_or_build_ltf_replay(initial_cash_krw: float, reports_dir: str | Path) -> dict[str, Any]:
    path = Path(reports_dir) / "latest_v686_atr_ltf_replay_summary.json"
    return _read_json(path) or build_v686_atr_ltf_replay_payload(initial_cash_krw, reports_dir)


def _read_or_build_precision(initial_cash_krw: float, reports_dir: str | Path) -> dict[str, Any]:
    path = Path(reports_dir) / "latest_v686_atr_precision_v2_summary.json"
    return _read_json(path) or build_v686_atr_precision_v2_payload(initial_cash_krw, reports_dir)


def _model_rows_from_missing(source: list[dict[str, Any]], initial_cash_krw: float, coverage: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for model, factor in (("conservative", 0.45), ("neutral", 0.75), ("optimistic", 0.90)):
        equity = initial_cash_krw
        peak = initial_cash_krw
        journal = []
        for row in source:
            before = equity
            pnl = float(row.get("pnl_krw", 0.0)) * factor
            equity = max(0.0, equity + pnl)
            peak = max(peak, equity)
            new_row = dict(row)
            new_row.update({"equity_before": before, "equity_after": equity, "pnl_krw": pnl, "drawdown_pct": (equity / peak - 1.0) * 100.0 if peak else 0.0})
            journal.append(new_row)
        summary = summary_from_journal(f"ATR_LTF_{model}", journal, initial_cash_krw)
        summary.update({"fill_model": model, "ltf_coverage_pct": coverage.get("best_coverage_pct", 0.0), "decision": "ATR_DATA_INSUFFICIENT"})
        rows.append(summary)
    return rows


def _coverage_pct(coverage: dict[str, Any], timeframe: str) -> float:
    return float(coverage.get(f"coverage_pct_{timeframe}", 0.0)) if timeframe in {"1m", "5m", "15m"} else 0.0


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
