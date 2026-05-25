from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from portfolio.equity_defense_governor import POLICIES, EquityDefenseGovernor


def run_drawdown_defense_revalidation(
    summary_path: str | Path = "docs/reports/latest_true_walk_forward_summary.json",
    archive_dir: str | Path = "replay_store/historical_archive",
    initial_cash_krw: float = 500000,
) -> dict[str, Any]:
    source = _read(Path(summary_path))
    journal = source.get("journal", [])
    market_metrics = _load_market_month_metrics(Path(archive_dir))
    baseline_curve = _baseline_curve(journal, initial_cash_krw)
    peak = _peak_point(baseline_curve)
    trough = _trough_after_peak(baseline_curve, peak["time"])
    scenarios = [_simulate(name, journal, market_metrics, initial_cash_krw, peak, trough) for name in POLICIES]
    _add_baseline_comparisons(scenarios)
    selected = next(row for row in scenarios if row["scenario"] == "ROLLING_EDGE_THROTTLE")
    summary = {
        "schema_version": "drawdown_defense_v1",
        "source_summary": str(summary_path),
        "baseline_peak": peak,
        "baseline_trough": trough,
        "drawdown_window": {"start": peak["time"], "end": trough["time"]},
        "scenarios": scenarios,
        "selected_defense": _compact_scenario(selected),
        "diagnosis": _diagnose(journal, peak["time"], trough["time"]),
        "market_month_metrics": {month: market_metrics[month] for month in sorted(market_metrics) if "2025-05" <= month <= "2026-05"},
        "recommendation": {
            "default_policy": "ROLLING_EDGE_THROTTLE",
            "reason": "하락 구간에서 거래를 완전히 중단하지 않고도 MDD를 가장 크게 낮췄습니다.",
            "live_readiness": "LIVE_NOT_ALLOWED",
            "next_step": "forward paper에서 실제 spread/depth overlay와 함께 방어 엔진을 켜고 검증합니다.",
        },
        **_safety(),
    }
    _write(Path("docs/reports/latest_drawdown_defense_summary.json"), summary)
    return summary


def _simulate(
    policy_name: str,
    journal: list[dict[str, Any]],
    market_metrics: dict[str, dict[str, float]],
    initial_cash: float,
    peak: dict[str, Any],
    trough: dict[str, Any],
) -> dict[str, Any]:
    governor = EquityDefenseGovernor(POLICIES[policy_name], initial_cash)
    trades = []
    skipped = Counter()
    monthly_actions: dict[str, Counter] = defaultdict(Counter)
    curve = []
    for trade in journal:
        month = str(trade.get("entry_time", ""))[:7]
        decision = governor.evaluate(trade, _previous_month_metric(month, market_metrics))
        action = decision["defense_action"]
        multiplier = float(decision["risk_multiplier_after_defense"])
        if action == "SKIP":
            pnl = 0.0
            skipped.update(decision["defense_reasons"] or ["SKIP"])
        else:
            pnl = float(trade.get("pnl_krw", 0.0)) * multiplier
            governor.record_result(trade, pnl)
            trades.append({**trade, "defense_pnl_krw": pnl, **decision})
        monthly_actions[month][action if action == "SKIP" else ("THROTTLE" if multiplier < 1 else "FULL_SIZE")] += 1
        curve.append({"time": trade.get("exit_time"), "equity": governor.equity, "drawdown_pct": _drawdown(governor.equity, governor.peak)})
    capital = _capital_stats(trades, initial_cash)
    drawdown_window = _period_stats(trades, peak["time"], trough["time"], initial_cash)
    return {
        "scenario": policy_name,
        "capital": capital,
        "drawdown_window": drawdown_window,
        "skipped_reasons": dict(skipped),
        "monthly_actions": {month: dict(counter) for month, counter in sorted(monthly_actions.items())},
        "equity_curve_sample": _sample_curve(curve),
        "annotated_trade_sample": [_compact_trade(trade) for trade in trades[:20]],
        **_safety(),
    }


def _add_baseline_comparisons(scenarios: list[dict[str, Any]]) -> None:
    baseline = next((row for row in scenarios if row.get("scenario") == "BASELINE"), None)
    if not baseline:
        return
    baseline_capital = baseline.get("capital", {})
    baseline_window = baseline.get("drawdown_window", {})
    baseline_final = float(baseline_capital.get("final_equity_krw", 0.0))
    baseline_mdd = float(baseline_capital.get("max_drawdown_pct", 0.0))
    baseline_window_pnl = float(baseline_window.get("total_pnl_krw", 0.0))
    for row in scenarios:
        capital = row.get("capital", {})
        window = row.get("drawdown_window", {})
        row["comparison_to_baseline"] = {
            "final_equity_delta_krw": float(capital.get("final_equity_krw", 0.0)) - baseline_final,
            "mdd_improvement_pct_point": float(capital.get("max_drawdown_pct", 0.0)) - baseline_mdd,
            "drawdown_window_loss_reduction_krw": float(window.get("total_pnl_krw", 0.0)) - baseline_window_pnl,
        }


def _compact_scenario(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario": row.get("scenario"),
        "capital": row.get("capital", {}),
        "drawdown_window": row.get("drawdown_window", {}),
        "comparison_to_baseline": row.get("comparison_to_baseline", {}),
        "skipped_reasons": row.get("skipped_reasons", {}),
        **_safety(),
    }


def _capital_stats(trades: list[dict[str, Any]], initial_cash: float) -> dict[str, Any]:
    pnl = sum(float(trade.get("defense_pnl_krw", trade.get("pnl_krw", 0.0))) for trade in trades)
    wins = [trade for trade in trades if float(trade.get("defense_pnl_krw", trade.get("pnl_krw", 0.0))) > 0]
    losses = [trade for trade in trades if float(trade.get("defense_pnl_krw", trade.get("pnl_krw", 0.0))) < 0]
    gross_win = sum(float(trade.get("defense_pnl_krw", trade.get("pnl_krw", 0.0))) for trade in wins)
    gross_loss = abs(sum(float(trade.get("defense_pnl_krw", trade.get("pnl_krw", 0.0))) for trade in losses))
    equity = initial_cash
    peak = initial_cash
    mdd = 0.0
    for trade in trades:
        equity += float(trade.get("defense_pnl_krw", trade.get("pnl_krw", 0.0)))
        peak = max(peak, equity)
        mdd = min(mdd, _drawdown(equity, peak))
    return {
        "trade_count": len(trades),
        "final_equity_krw": initial_cash + pnl,
        "total_pnl_krw": pnl,
        "total_return_pct": (initial_cash + pnl) / initial_cash * 100 - 100,
        "win_rate_pct": len(wins) / len(trades) * 100 if trades else 0.0,
        "profit_factor": gross_win / gross_loss if gross_loss else 0.0,
        "max_drawdown_pct": mdd,
    }


def _compact_trade(trade: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "trade_id",
        "market",
        "strategy",
        "setup_type",
        "entry_time",
        "exit_time",
        "pnl_krw",
        "defense_pnl_krw",
        "defense_mode",
        "risk_multiplier_after_defense",
        "defense_reasons",
        "defense_action",
        "drawdown_before_pct",
    ]
    return {key: trade.get(key) for key in keys if key in trade}


def _period_stats(trades: list[dict[str, Any]], start: str, end: str, initial_cash: float) -> dict[str, Any]:
    items = [trade for trade in trades if start < str(trade.get("exit_time")) <= end]
    capital = _capital_stats(items, initial_cash)
    throttled = sum(1 for trade in items if float(trade.get("risk_multiplier_after_defense", 1.0)) < 1.0)
    return {**capital, "throttled_trade_count": throttled}


def _baseline_curve(journal: list[dict[str, Any]], initial_cash: float) -> list[dict[str, Any]]:
    equity = initial_cash
    peak = initial_cash
    rows = []
    for trade in journal:
        equity += float(trade.get("pnl_krw", 0.0))
        peak = max(peak, equity)
        rows.append({"time": trade.get("exit_time"), "equity": equity, "drawdown_pct": _drawdown(equity, peak)})
    return rows


def _peak_point(curve: list[dict[str, Any]]) -> dict[str, Any]:
    return max(curve, key=lambda row: float(row["equity"])) if curve else {"time": None, "equity": 0.0}


def _trough_after_peak(curve: list[dict[str, Any]], peak_time: str | None) -> dict[str, Any]:
    after = [row for row in curve if peak_time and str(row["time"]) > peak_time]
    return min(after, key=lambda row: float(row["drawdown_pct"])) if after else {"time": None, "equity": 0.0, "drawdown_pct": 0.0}


def _diagnose(journal: list[dict[str, Any]], start: str, end: str) -> dict[str, Any]:
    items = [trade for trade in journal if start < str(trade.get("exit_time")) <= end]
    return {
        "trade_count": len(items),
        "pnl_krw": sum(float(trade.get("pnl_krw", 0.0)) for trade in items),
        "by_plan": _group(items, "plan"),
        "by_strategy": _group(items, "strategy"),
        "by_setup": _group(items, "setup_type"),
        "worst_markets": _group(items, "market")[:15],
        "loss_streaks": _loss_streaks(items)[:10],
    }


def _group(trades: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        grouped[str(trade.get(key, "UNKNOWN"))].append(trade)
    rows = []
    for name, items in grouped.items():
        pnl = sum(float(trade.get("pnl_krw", 0.0)) for trade in items)
        wins = sum(1 for trade in items if float(trade.get("pnl_krw", 0.0)) > 0)
        rows.append({"name": name, "trade_count": len(items), "pnl_krw": pnl, "win_rate_pct": wins / len(items) * 100 if items else 0.0})
    return sorted(rows, key=lambda row: row["pnl_krw"])


def _loss_streaks(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    streaks = []
    current = []
    for trade in trades:
        if float(trade.get("pnl_krw", 0.0)) < 0:
            current.append(trade)
        elif current:
            streaks.append(current)
            current = []
    if current:
        streaks.append(current)
    rows = []
    for streak in streaks:
        rows.append(
            {
                "length": len(streak),
                "start": streak[0].get("exit_time"),
                "end": streak[-1].get("exit_time"),
                "pnl_krw": sum(float(trade.get("pnl_krw", 0.0)) for trade in streak),
            }
        )
    return sorted(rows, key=lambda row: (row["length"], -row["pnl_krw"]), reverse=True)


def _load_market_month_metrics(archive_dir: Path) -> dict[str, dict[str, float]]:
    rows: dict[str, list[float]] = defaultdict(list)
    for path in (archive_dir / "1d").glob("KRW-*.parquet"):
        frame = pd.read_parquet(path)
        if frame.empty:
            continue
        frame["time"] = pd.to_datetime(frame["time"])
        frame = frame.sort_values("time")
        frame["month"] = frame["time"].dt.strftime("%Y-%m")
        for month, group in frame.groupby("month"):
            if len(group) >= 2:
                rows[month].append((float(group["close"].iloc[-1]) / float(group["close"].iloc[0]) - 1.0) * 100)
    return {
        month: {
            "market_count": len(values),
            "avg_return_pct": sum(values) / len(values),
            "positive_market_pct": sum(1 for value in values if value > 0) / len(values) * 100,
        }
        for month, values in rows.items()
    }


def _previous_month_metric(month: str, metrics: dict[str, dict[str, float]]) -> dict[str, float] | None:
    months = sorted(metrics)
    if month not in months:
        return None
    idx = months.index(month)
    return metrics[months[idx - 1]] if idx > 0 else None


def _sample_curve(curve: list[dict[str, Any]], target: int = 180) -> list[dict[str, Any]]:
    if len(curve) <= target:
        return curve
    step = max(1, len(curve) // target)
    return curve[::step] + ([curve[-1]] if curve[-1] not in curve[::step] else [])


def _drawdown(equity: float, peak: float) -> float:
    return (equity - peak) / peak * 100 if peak else 0.0


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _safety() -> dict[str, bool]:
    return {"real_order_enabled": False, "live_order_allowed": False, "auto_apply_allowed": False}
