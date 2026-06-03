from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from scenario_telemetry.v688_common import ACTIVE_ROUTE, daily_rows_from_backfill, load_context, profit_factor, safe_status, win_rate, write_json


def build_scenario_telemetry(
    initial_cash_krw: float = 500000.0,
    use_available_history: bool = True,
    reports_dir: str | Path = "docs/reports",
    data_dir: str | Path = "data/paper",
) -> dict[str, Any]:
    ctx = load_context(reports_dir, data_dir)
    backfill = ctx["backfill"]
    daily = _daily_rows(ctx, backfill)
    weekly = _aggregate(daily, "week")
    monthly = _aggregate(daily, "month")
    reports = Path(reports_dir)
    base = {
        "schema_version": "v688_scenario_telemetry_v1",
        "initial_cash_krw": initial_cash_krw,
        "use_available_history": bool(use_available_history),
        "data_sources": ["historical_backfill", "forward_candidate_log", "paper_trade", "equity_snapshot"],
        **safe_status(),
    }
    daily_payload = write_json(reports / "latest_v688_scenario_daily_summary.json", {**base, "rows": daily, "row_count": len(daily)})
    weekly_payload = write_json(reports / "latest_v688_scenario_weekly_summary.json", {**base, "rows": weekly, "row_count": len(weekly)})
    monthly_payload = write_json(reports / "latest_v688_scenario_monthly_summary.json", {**base, "rows": monthly, "row_count": len(monthly)})
    from scenario_telemetry.scenario_telemetry_report_builder import build_scenario_telemetry_report

    build_scenario_telemetry_report(reports)
    return {"daily": daily_payload, "weekly": weekly_payload, "monthly": monthly_payload, **safe_status()}


def _daily_rows(ctx: dict[str, Any], backfill: dict[str, Any]) -> list[dict[str, Any]]:
    rows = daily_rows_from_backfill(backfill, backfill.get("active_route") or ACTIVE_ROUTE)
    forward_events = ctx["forward_events"]
    if forward_events:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in forward_events:
            grouped[str(event.get("date") or date.today().isoformat())].append(event)
        for day, events in grouped.items():
            reasons = [event.get("primary_block_reason") for event in events if event.get("primary_block_reason")]
            rows.append(
                {
                    "date": day,
                    "scenario_id": ACTIVE_ROUTE,
                    "route_status": "ACTIVE",
                    "market_state": "FORWARD_MICRO",
                    "candidates_seen": len(events),
                    "enter_count": len([e for e in events if e.get("entry_decision") == "ENTER"]),
                    "wait_count": len([e for e in events if e.get("entry_decision") == "WAIT"]),
                    "skip_count": len([e for e in events if e.get("entry_decision") not in {"ENTER", "WAIT"}]),
                    "exit_count": 0,
                    "realized_pnl_krw": 0.0,
                    "unrealized_pnl_krw": 0.0,
                    "daily_return_pct": 0.0,
                    "max_intraday_drawdown": None,
                    "top_skip_reasons": _top(reasons),
                    "top_entry_reasons": [],
                    "top_exit_reasons": [],
                    "guard_on_count": 0,
                    "hard_guard_count": 0,
                    "dominance_risk_count": 0,
                    "avg_expected_rr": None,
                    "avg_realized_rr": None,
                    "missed_opportunity_count": len(events),
                    "false_entry_count": 0,
                    "data_quality_flags": ["FORWARD_CANDIDATE_ONLY", "NO_LEDGER_UPDATE"],
                }
            )
    for row in rows:
        row.setdefault("candidates_seen", row.get("candidate_count", row.get("trade_count", 0)))
        row.setdefault("unrealized_pnl_krw", 0.0)
        row.setdefault("top_skip_reasons", [])
        row.setdefault("top_entry_reasons", [])
        row.setdefault("top_exit_reasons", [])
        row.setdefault("guard_on_count", 0)
        row.setdefault("hard_guard_count", 0)
        row.setdefault("dominance_risk_count", 0)
        row.setdefault("avg_expected_rr", None)
        row.setdefault("avg_realized_rr", None)
        row.setdefault("missed_opportunity_count", 0)
        row.setdefault("false_entry_count", 0)
    return sorted(rows, key=lambda row: str(row.get("date", "")))


def _aggregate(rows: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        day = str(row.get("date", ""))
        if kind == "month":
            period = day[:7]
        else:
            try:
                parsed = date.fromisoformat(day[:10])
                period = f"{parsed.isocalendar().year}-W{parsed.isocalendar().week:02d}"
            except ValueError:
                period = day[:7]
        groups[(str(row.get("scenario_id")), period)].append(row)
    out = []
    for (scenario, period), items in sorted(groups.items(), key=lambda item: item[0]):
        pnl_values = [float(item.get("realized_pnl_krw", 0.0) or 0.0) for item in items]
        trade_count = sum(int(item.get("enter_count", item.get("trade_count", 0)) or 0) for item in items)
        candidate_count = sum(int(item.get("candidates_seen", 0) or 0) for item in items)
        row = {
            ("month" if kind == "month" else "week"): period,
            "scenario_id": scenario,
            "market_state_distribution": _distribution(items),
            ("monthly_pnl" if kind == "month" else "weekly_pnl"): sum(pnl_values),
            ("monthly_return_pct" if kind == "month" else "weekly_return_pct"): sum(float(item.get("daily_return_pct", 0.0) or 0.0) for item in items),
            "MDD": min([float(item.get("max_intraday_drawdown") or 0.0) for item in items] or [0.0]),
            "PF": profit_factor(pnl_values),
            "win_rate": win_rate(pnl_values),
            "trade_count": trade_count,
            "candidate_count": candidate_count,
            "enter_rate": (trade_count / candidate_count * 100.0) if candidate_count else 0.0,
            "skip_rate": 100.0 - ((trade_count / candidate_count * 100.0) if candidate_count else 0.0),
            "best_market_state": _best_state(items),
            "worst_market_state": _worst_state(items),
            "active_vs_shadow_delta": None,
            "failure_signatures": _failures(items),
            "recommendation_flags": ["PAPER_MORE_REQUIRED"] if candidate_count < 30 else [],
        }
        if kind == "month":
            row.update(
                {
                    "return_mdd_ratio": (row["monthly_return_pct"] / abs(row["MDD"])) if row["MDD"] else None,
                    "saved_loss": 0.0,
                    "missed_profit": 0.0,
                    "net_effect": row["monthly_pnl"],
                    "profit_giveback_ratio": None,
                    "best_window_type": row["best_market_state"],
                    "worst_window_type": row["worst_market_state"],
                    "promotion_score": max(row["monthly_return_pct"], 0.0),
                    "demotion_score": abs(min(row["monthly_return_pct"], 0.0)),
                    "recommendation": "MANUAL_REVIEW_REQUIRED",
                }
            )
        out.append(row)
    return out


def _top(values: list[Any]) -> list[dict[str, Any]]:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        counts[str(value)] += 1
    return [{"reason": key, "count": count} for key, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:3]]


def _distribution(items: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for item in items:
        out[str(item.get("market_state", "UNKNOWN"))] += 1
    return dict(out)


def _best_state(items: list[dict[str, Any]]) -> str:
    return _state_by_pnl(items, reverse=True)


def _worst_state(items: list[dict[str, Any]]) -> str:
    return _state_by_pnl(items, reverse=False)


def _state_by_pnl(items: list[dict[str, Any]], reverse: bool) -> str:
    totals: dict[str, float] = defaultdict(float)
    for item in items:
        totals[str(item.get("market_state", "UNKNOWN"))] += float(item.get("realized_pnl_krw", 0.0) or 0.0)
    if not totals:
        return "UNKNOWN"
    return sorted(totals.items(), key=lambda item: item[1], reverse=reverse)[0][0]


def _failures(items: list[dict[str, Any]]) -> list[str]:
    failures = []
    if any("NO_LEDGER_UPDATE" in item.get("data_quality_flags", []) for item in items):
        failures.append("candidate_to_ledger_gap")
    if sum(int(item.get("candidates_seen", 0) or 0) for item in items) and not sum(int(item.get("enter_count", 0) or 0) for item in items):
        failures.append("candidate_starvation")
    return failures
