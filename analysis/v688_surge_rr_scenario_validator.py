from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from analysis.v687_investment_pattern_validator import (
    _dd_bucket,
    _join_trades_decisions,
    _latest_run_id,
    _month_bucket,
    _pf_bucket,
    _read_json,
    _read_jsonl,
    _reason_bucket,
)
from paper_runtime.live_order_guard import assert_live_orders_disabled
from paper_runtime.paper_runtime_schema import safety_flags


SCENARIOS = ("SRR_STRICT_WF", "SRR_BALANCED_WF", "SRR_AGGRESSIVE_WF")


def run_v688_surge_rr_scenario_validation(
    initial_cash_krw: float = 500000.0,
    start_date: str = "2026-01-01",
    reports_dir: str | Path = "docs/reports",
    data_dir: str | Path = "data/paper",
    output_name: str = "latest_v688_surge_rr_scenario_summary.json",
) -> dict[str, Any]:
    assert_live_orders_disabled()
    reports = Path(reports_dir)
    data = Path(data_dir)
    backfill = _read_json(reports / "latest_v683_backfill_20260101_summary.json")
    trades = _read_jsonl(data / "journal" / "paper_trades.jsonl")
    latest_run_id = _latest_run_id(trades) or str(backfill.get("run_id") or "")
    trades = [row for row in trades if str(row.get("trade_id", "")).startswith(latest_run_id)]
    decisions = [row for row in _read_jsonl(data / "journal" / "paper_decisions.jsonl") if str(row.get("decision_id", "")).startswith(latest_run_id)]
    rows = [row for row in _join_trades_decisions(trades, decisions) if str(row.get("date", "")) >= start_date]
    learned = _learn_rule_sets(rows)
    scenario_journals = {scenario: _simulate_walk_forward(scenario, rows, initial_cash_krw, learned[scenario]) for scenario in SCENARIOS}
    oracle_journals = {scenario.replace("_WF", "_ORACLE"): _simulate_oracle(scenario.replace("_WF", "_ORACLE"), rows, initial_cash_krw, learned[scenario]) for scenario in SCENARIOS}
    routes = [_summary(route, journal, initial_cash_krw, "WALK_FORWARD") for route, journal in scenario_journals.items()]
    oracle_routes = [_summary(route, journal, initial_cash_krw, "ORACLE_REFERENCE") for route, journal in oracle_journals.items()]
    active = next((row for row in backfill.get("routes", []) if row.get("scenario") == backfill.get("active_route")), {})
    best = max(routes, key=lambda row: (float(row.get("return_pct", -999.0)), float(row.get("mdd_pct", -999.0))), default={})
    payload = {
        "schema_version": "v688_surge_rr_scenario_v1",
        "generated_at": datetime.utcnow().isoformat(),
        "source_backfill_run_id": backfill.get("run_id"),
        "journal_run_id_used": latest_run_id,
        "start_date": start_date,
        "initial_cash_krw": initial_cash_krw,
        "source_trade_count": len(rows),
        "scenario_definition": {
            "goal": "수익률 급등 패턴과 손익비 우수 패턴만 골라 진입하는 shadow paper 시나리오",
            "surge": "pnl_pct >= 0.50 거래가 자주 나온 조합",
            "risk_reward": "PF, 평균이익/평균손실, 기대손익이 동시에 양호한 조합",
            "walk_forward": "해당 월 이전 데이터로만 규칙을 배우고 해당 월에 적용",
            "oracle_warning": "oracle은 전체 기간을 보고 만든 참고값이라 주 시나리오 승격 근거로 쓰지 않음",
        },
        "learned_rule_counts": {scenario: _rule_count(rules) for scenario, rules in learned.items()},
        "active_baseline": active,
        "routes": routes,
        "oracle_reference_routes": oracle_routes,
        "daily_equity": {route: _period_rows(journal, "day") for route, journal in scenario_journals.items()},
        "weekly_returns": {route: _period_rows(journal, "week") for route, journal in scenario_journals.items()},
        "monthly_returns": {route: _period_rows(journal, "month") for route, journal in scenario_journals.items()},
        "best_walk_forward_route": best.get("scenario"),
        "promotion_check": _promotion_check(best, active),
        "decision": "SURGE_RR_SHADOW_VALIDATED" if _can_promote(best, active) else "SURGE_RR_RESEARCH_ONLY",
        **safety_flags(),
    }
    _write(reports / output_name, payload)
    return payload


def _learn_rule_sets(rows: list[dict[str, Any]]) -> dict[str, dict[str, set[tuple[str, ...]]]]:
    months = sorted({str(row.get("month", "")) for row in rows if row.get("month")})
    learned = {scenario: {} for scenario in SCENARIOS}
    for month in months:
        train = [row for row in rows if str(row.get("month", "")) < month]
        for scenario in SCENARIOS:
            learned[scenario][month] = _select_rules(train, scenario)
    return learned


def _select_rules(rows: list[dict[str, Any]], scenario: str) -> dict[str, set[tuple[str, ...]]]:
    if not rows:
        return {"surge": set(), "risk_reward": set()}
    if scenario == "SRR_STRICT_WF":
        cfg = {"min_trades": 8, "min_pf": 2.0, "min_rr": 1.5, "min_total": 1.0, "min_surge": 30.0}
    elif scenario == "SRR_BALANCED_WF":
        cfg = {"min_trades": 6, "min_pf": 1.4, "min_rr": 1.4, "min_total": 1.0, "min_surge": 15.0}
    else:
        cfg = {"min_trades": 5, "min_pf": 1.15, "min_rr": 1.2, "min_total": 1.0, "min_surge": 10.0}
    return {"surge": _good_surge_keys(rows, cfg), "risk_reward": _good_rr_keys(rows, cfg)}


def _simulate_walk_forward(
    scenario: str,
    rows: list[dict[str, Any]],
    initial_cash_krw: float,
    learned: dict[str, dict[str, set[tuple[str, ...]]]],
) -> list[dict[str, Any]]:
    equity = initial_cash_krw
    peak = initial_cash_krw
    journal = []
    for row in rows:
        month_rules = learned.get(str(row.get("month", "")), {"surge": set(), "risk_reward": set()})
        enter, reason = _enter_decision(row, month_rules)
        before = equity
        pnl = 0.0
        position_krw = 0.0
        if enter:
            allocation = min(max(float(row.get("size_krw", 0.0) or 0.0) / initial_cash_krw, 0.0), 1.0)
            position_krw = equity * allocation
            pnl = position_krw * float(row.get("pnl_pct", 0.0) or 0.0) / 100.0
            equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        journal.append(_journal_row(scenario, row, before, equity, peak, pnl, position_krw, enter, reason))
    return journal


def _simulate_oracle(
    scenario: str,
    rows: list[dict[str, Any]],
    initial_cash_krw: float,
    learned: dict[str, dict[str, set[tuple[str, ...]]]],
) -> list[dict[str, Any]]:
    all_rules = _select_rules(rows, scenario.replace("_ORACLE", "_WF"))
    months = {str(row.get("month", "")) for row in rows if row.get("month")}
    return _simulate_walk_forward(scenario, rows, initial_cash_krw, {month: all_rules for month in months})


def _enter_decision(row: dict[str, Any], rules: dict[str, set[tuple[str, ...]]]) -> tuple[bool, list[str]]:
    reasons = []
    if _surge_key(row) in rules.get("surge", set()):
        reasons.append("SURGE_PATTERN_PASS")
    if _rr_key(row) in rules.get("risk_reward", set()):
        reasons.append("RISK_REWARD_PASS")
    return bool(reasons), reasons or ["NO_SURGE_RR_EDGE"]


def _good_surge_keys(rows: list[dict[str, Any]], cfg: dict[str, float]) -> set[tuple[str, ...]]:
    buckets: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[_surge_key(row)].append(row)
    out = set()
    for key, items in buckets.items():
        summary = _trade_summary(items)
        surge_rate = sum(1 for row in items if float(row.get("pnl_pct", 0.0) or 0.0) >= 0.50) / len(items) * 100.0
        if _passes(summary, items, cfg) and surge_rate >= cfg["min_surge"]:
            out.add(key)
    return out


def _good_rr_keys(rows: list[dict[str, Any]], cfg: dict[str, float]) -> set[tuple[str, ...]]:
    buckets: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[_rr_key(row)].append(row)
    return {key for key, items in buckets.items() if _passes(_trade_summary(items), items, cfg)}


def _passes(summary: dict[str, Any], items: list[dict[str, Any]], cfg: dict[str, float]) -> bool:
    return (
        len(items) >= cfg["min_trades"]
        and summary["total_pnl_krw"] > cfg["min_total"]
        and summary["profit_factor"] >= cfg["min_pf"]
        and summary["avg_win_loss_ratio"] >= cfg["min_rr"]
        and summary["expectancy_krw"] > 0.0
    )


def _surge_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row.get("market_state") or "UNKNOWN"),
        "DOM_RISK" if row.get("dominance_risk") else "DOM_OK",
        _pf_bucket(row.get("pf20")),
        _month_bucket(row.get("month_return_pct")),
        _dd_bucket(row.get("hwm_drawdown_pct")),
        str(row.get("action") or "UNKNOWN"),
    )


def _rr_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row.get("market_state") or "UNKNOWN"),
        _pf_bucket(row.get("pf20")),
        _dd_bucket(row.get("hwm_drawdown_pct")),
        _reason_bucket(row.get("reason")),
    )


def _journal_row(
    scenario: str,
    source: dict[str, Any],
    before: float,
    after: float,
    peak: float,
    pnl: float,
    position_krw: float,
    enter: bool,
    reasons: list[str],
) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "date": str(source.get("date", "")),
        "decision_time": source.get("time"),
        "entry_time": source.get("entry_time"),
        "exit_time": source.get("exit_time"),
        "market": source.get("market"),
        "defense_action": "ENTER" if enter else "SKIP",
        "defense_reasons": reasons,
        "position_krw": position_krw,
        "pnl_krw": pnl,
        "return_pct": float(source.get("pnl_pct", 0.0) or 0.0) if enter else 0.0,
        "equity_before": before,
        "equity_after": after,
        "drawdown_pct": (after / peak - 1.0) * 100.0 if peak else 0.0,
        "source_trade_id": source.get("trade_id"),
        "source_market_state": source.get("market_state"),
        "source_action": source.get("action"),
        "source_pf20": source.get("pf20"),
        "source_month_return_pct": source.get("month_return_pct"),
        "source_hwm_drawdown_pct": source.get("hwm_drawdown_pct"),
    }


def _summary(route: str, journal: list[dict[str, Any]], initial_cash_krw: float, mode: str) -> dict[str, Any]:
    entered = [row for row in journal if row.get("defense_action") == "ENTER"]
    pnls = [float(row.get("pnl_krw", 0.0) or 0.0) for row in entered]
    wins = [pnl for pnl in pnls if pnl > 0.0]
    losses = [pnl for pnl in pnls if pnl < 0.0]
    final = float(journal[-1].get("equity_after", initial_cash_krw)) if journal else initial_cash_krw
    gross_loss = abs(sum(losses))
    return {
        "scenario": route,
        "route_status": "SHADOW",
        "source_mode": mode,
        "initial_cash_krw": initial_cash_krw,
        "final_equity_krw": final,
        "return_pct": (final / initial_cash_krw - 1.0) * 100.0 if initial_cash_krw else 0.0,
        "mdd_pct": min([0.0] + [float(row.get("drawdown_pct", 0.0) or 0.0) for row in journal]),
        "profit_factor": sum(wins) / gross_loss if gross_loss else 99.0 if wins else 0.0,
        "avg_win_loss_ratio": (mean(wins) / abs(mean(losses))) if wins and losses else 99.0 if wins else 0.0,
        "win_rate_pct": len(wins) / len(entered) * 100.0 if entered else 0.0,
        "trade_count": len(entered),
        "skipped_trade_count": len(journal) - len(entered),
        "decision": "SURGE_RR_SHADOW",
        "lookahead_fail_count": 0 if mode == "WALK_FORWARD" else 1,
    }


def _period_rows(journal: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        date = str(row.get("date", ""))
        if mode == "day":
            key = date[:10]
        elif mode == "week":
            try:
                dt = datetime.fromisoformat(date[:10])
                iso = dt.isocalendar()
                key = f"{iso.year}-W{iso.week:02d}"
            except ValueError:
                key = date[:10]
        else:
            key = date[:7]
        groups[key].append(row)
    out = []
    for period in sorted(groups):
        items = groups[period]
        start = float(items[0].get("equity_before", 0.0) or 0.0)
        end = float(items[-1].get("equity_after", start) or start)
        out.append(
            {
                "period": period,
                "trade_count": sum(1 for item in items if item.get("defense_action") == "ENTER"),
                "start_equity_krw": start,
                "end_equity_krw": end,
                "pnl_krw": end - start,
                "return_pct": (end / start - 1.0) * 100.0 if start else 0.0,
                "mdd_pct": min([0.0] + [float(item.get("drawdown_pct", 0.0) or 0.0) for item in items]),
            }
        )
    return out


def _trade_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pnls = [float(row.get("pnl_krw", 0.0) or 0.0) for row in rows]
    wins = [pnl for pnl in pnls if pnl > 0.0]
    losses = [pnl for pnl in pnls if pnl < 0.0]
    gross_loss = abs(sum(losses))
    return {
        "total_pnl_krw": sum(pnls),
        "profit_factor": sum(wins) / gross_loss if gross_loss else 99.0 if wins else 0.0,
        "avg_win_loss_ratio": (mean(wins) / abs(mean(losses))) if wins and losses else 99.0 if wins else 0.0,
        "expectancy_krw": mean(pnls) if pnls else 0.0,
    }


def _promotion_check(best: dict[str, Any], active: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate": best.get("scenario"),
        "beats_active_return": float(best.get("return_pct", -999.0) or -999.0) > float(active.get("return_pct", -999.0) or -999.0),
        "beats_or_matches_active_mdd": float(best.get("mdd_pct", -999.0) or -999.0) >= float(active.get("mdd_pct", -999.0) or -999.0),
        "trade_count_ok": int(best.get("trade_count", 0) or 0) >= 20,
        "lookahead_clean": int(best.get("lookahead_fail_count", 1)) == 0,
        "auto_apply_allowed": False,
    }


def _can_promote(best: dict[str, Any], active: dict[str, Any]) -> bool:
    check = _promotion_check(best, active)
    return bool(check["beats_active_return"] and check["beats_or_matches_active_mdd"] and check["trade_count_ok"] and check["lookahead_clean"])


def _rule_count(rules_by_month: dict[str, dict[str, set[tuple[str, ...]]]]) -> dict[str, int]:
    return {month: sum(len(value) for value in rules.values()) for month, rules in rules_by_month.items()}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(run_v688_surge_rr_scenario_validation(), ensure_ascii=False, default=str))
