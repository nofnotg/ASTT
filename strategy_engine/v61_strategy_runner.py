from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.big_win_dependency_analyzer import analyze_big_win_dependency
from analysis.regime_performance_analyzer import analyze_regime_performance
from analysis.risk_parameter_sweep import run_risk_parameter_sweep_rows
from analysis.strategy_failure_reason_analyzer import analyze_strategy_failure
from analysis.strategy_success_reason_analyzer import analyze_strategy_success
from execution.v6_paper_entry_runner import run_v6_strategy_backtest
from execution.v6_position_manager import summarize_v6_trades
from strategy_engine.v61_strategy_decision import decide_strategy
from strategy_engine.v61_strategy_registry import V61_SETUP_STRATEGIES, V61_STRATEGIES
from strategy_engine.v61_setup_filter_policy import setup_decision
from validation.data_split_validator import split_trades_train_validation_test
from validation.lookahead_bias_checker import audit_trades_for_lookahead


def run_v61_strategy_robustness(months: int = 36, initial_cash_krw: float = 500000, paper_entry_policy: str = "ACTIVE_RESEARCH") -> dict[str, Any]:
    strategy_summaries = [run_v6_strategy_backtest(strategy, months, initial_cash_krw, paper_entry_policy) for strategy in V61_STRATEGIES]
    rows = []
    for summary in strategy_summaries:
        trades = summary.get("trades", [])
        dependency = analyze_big_win_dependency(summary["strategy"], trades, initial_cash_krw)
        split = split_trades_train_validation_test(trades, initial_cash_krw)
        rows.append({**_thin_summary(summary), "decision": decide_strategy(summary, dependency, split)})
    setup_rows = _setup_rows(strategy_summaries, initial_cash_krw)
    payload = {
        "schema_version": "v6.1",
        "requested_months": months,
        "paper_entry_policy": paper_entry_policy,
        "strategies": rows + setup_rows,
        "paper_trade_count": sum(row["trade_count"] for row in rows),
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
    _write("docs/reports/latest_v61_strategy_robustness_summary.json", payload)
    _write("replay_store/v61/latest_v61_strategy_robustness_summary.json", payload)
    return payload


def run_v61_regime_backtest(initial_cash_krw: float = 500000) -> dict[str, Any]:
    summaries = _load_v6_summaries()
    rows = []
    for summary in summaries:
        rows.extend(analyze_regime_performance(summary["strategy"], summary.get("trades", []), initial_cash_krw))
    payload = {"schema_version": "v6.1", "regime_rows": rows, "real_order_enabled": False, "live_order_allowed": False}
    _write("docs/reports/latest_v61_regime_summary.json", payload)
    _write("replay_store/v61/latest_v61_regime_summary.json", payload)
    return payload


def run_v61_big_win_dependency(initial_cash_krw: float = 500000) -> dict[str, Any]:
    rows = [analyze_big_win_dependency(summary["strategy"], summary.get("trades", []), initial_cash_krw) for summary in _load_v6_summaries()]
    payload = {"schema_version": "v6.1", "dependency_rows": rows, "real_order_enabled": False, "live_order_allowed": False}
    _write("docs/reports/latest_v61_big_win_dependency_summary.json", payload)
    _write("replay_store/v61/latest_v61_big_win_dependency_summary.json", payload)
    return payload


def run_v61_failure_success_analysis() -> dict[str, Any]:
    rows = []
    for summary in _load_v6_summaries():
        rows.append({
            "strategy": summary["strategy"],
            "success": analyze_strategy_success(summary["strategy"], summary.get("trades", [])),
            "failure": analyze_strategy_failure(summary["strategy"], summary.get("trades", [])),
        })
    payload = {"schema_version": "v6.1", "analysis_rows": rows, "real_order_enabled": False, "live_order_allowed": False}
    _write("docs/reports/latest_v61_failure_success_summary.json", payload)
    _write("replay_store/v61/latest_v61_failure_success_summary.json", payload)
    return payload


def run_v61_risk_sweep() -> dict[str, Any]:
    rows = run_risk_parameter_sweep_rows(_load_v6_summaries())
    payload = {"schema_version": "v6.1", "risk_rows": rows, "real_order_enabled": False, "live_order_allowed": False}
    _write("docs/reports/latest_v61_risk_sweep_summary.json", payload)
    _write("replay_store/v61/latest_v61_risk_sweep_summary.json", payload)
    return payload


def run_v61_train_test_validation(initial_cash_krw: float = 500000) -> dict[str, Any]:
    rows = []
    checks = []
    for summary in _load_v6_summaries():
        split = split_trades_train_validation_test(summary.get("trades", []), initial_cash_krw)
        audit = audit_trades_for_lookahead(summary.get("trades", []))
        rows.append({"strategy": summary["strategy"], **split})
        checks.append({"strategy": summary["strategy"], **audit})
    payload = {
        "schema_version": "v6.1",
        "split_rows": rows,
        "lookahead": _aggregate_lookahead(checks),
        "lookahead_by_strategy": checks,
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
    _write("docs/reports/latest_v61_train_test_summary.json", payload)
    _write("replay_store/v61/latest_v61_train_test_summary.json", payload)
    return payload


def build_v61_final_decision() -> dict[str, Any]:
    robustness = _read("docs/reports/latest_v61_strategy_robustness_summary.json")
    dependency = _read("docs/reports/latest_v61_big_win_dependency_summary.json")
    keep = [row["strategy"] for row in robustness.get("strategies", []) if row.get("decision") in {"STRATEGY_KEEP_FOR_FORWARD", "STRATEGY_KEEP_WITH_FILTER"}]
    disabled = [row["strategy"] for row in robustness.get("strategies", []) if row.get("decision") == "STRATEGY_DISABLE"]
    payload = {
        "schema_version": "v6.1",
        "forward_candidates": keep,
        "disabled_strategies": disabled,
        "dependency_summary": dependency.get("dependency_rows", []),
        "final_judgement": "PAPER_MORE_REQUIRED" if keep else "STRATEGY_REDESIGN_REQUIRED",
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write("docs/reports/latest_v61_final_decision_summary.json", payload)
    _write("replay_store/v61/latest_v61_final_decision_summary.json", payload)
    return payload


def _setup_rows(summaries: list[dict], initial_cash_krw: float) -> list[dict]:
    rows = []
    for summary in summaries:
        for setup, stats in summary.get("setup_stats", {}).items():
            if setup in V61_SETUP_STRATEGIES:
                rows.append({
                    "strategy": setup,
                    "trade_count": stats.get("trade_count", 0),
                    "win_rate": stats.get("win_rate", 0.0),
                    "profit_factor": stats.get("profit_factor"),
                    "expectancy_pct": stats.get("expectancy_pct", 0.0),
                    "total_return_pct": stats.get("total_return_pct", 0.0),
                    "max_drawdown_pct": summary.get("max_drawdown_pct", 0.0),
                    "decision": setup_decision(stats.get("expectancy_pct", 0.0), stats.get("trade_count", 0)),
                })
    present = {row["strategy"] for row in rows}
    for missing in sorted(set(V61_SETUP_STRATEGIES) - present):
        rows.append({"strategy": missing, **summarize_v6_trades([], initial_cash_krw), "max_drawdown_pct": 0.0, "decision": "DATA_OR_DETECTOR_FAILURE"})
    return rows


def _thin_summary(summary: dict) -> dict:
    keys = ["strategy", "trade_count", "win_rate", "profit_factor", "expectancy_pct", "total_return_pct", "max_drawdown_pct"]
    return {key: summary.get(key) for key in keys}


def _load_v6_summaries() -> list[dict]:
    return [
        _read("docs/reports/latest_v6_daddy_strategy_summary.json"),
        _read("docs/reports/latest_v6_ict_strategy_summary.json"),
        _read("docs/reports/latest_v6_combined_strategy_summary.json"),
    ]


def _aggregate_lookahead(rows: list[dict]) -> dict:
    return {
        "checked_trades": sum(row["checked_trades"] for row in rows),
        "pass": sum(row["pass"] for row in rows),
        "fail": sum(row["fail"] for row in rows),
        "excluded_trades": sum(row["excluded_trades"] for row in rows),
        "major_violations": sorted({item for row in rows for item in row["major_violations"]}),
    }


def _read(path: str) -> dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else {}


def _write(path: str, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
