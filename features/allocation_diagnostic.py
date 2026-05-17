from __future__ import annotations

from typing import Any

import pandas as pd


GRADE_ORDER = ["A_PLUS", "A", "B", "C", "REJECT", "PAPER_ONLY"]


def build_allocation_diagnostic(trades: pd.DataFrame, initial_equity_krw: float = 500000) -> dict[str, Any]:
    rows = _prepare_rows(trades, initial_equity_krw)
    if rows.empty:
        return {
            "rows": [],
            "grade_table": [],
            "good_trade_underallocated_count": 0,
            "bad_trade_overallocated_count": 0,
            "allocation_alpha_krw": 0.0,
            "summary": "no_trades",
        }
    grade_table = _grade_table(rows)
    good_under = int(((rows["trade_pnl_pct"] > 0) & (rows["allocation_pct"] < 0.5)).sum())
    bad_over = int(((rows["trade_pnl_pct"] < 0) & (rows["allocation_pct"] > 0.5)).sum())
    alpha = float(rows["allocation_alpha_krw"].sum())
    summary = "grade_based_helped" if alpha > 0 else "grade_based_hurt"
    return {
        "rows": rows.to_dict("records"),
        "grade_table": grade_table,
        "good_trade_underallocated_count": good_under,
        "bad_trade_overallocated_count": bad_over,
        "allocation_alpha_krw": alpha,
        "summary": summary,
    }


def _prepare_rows(trades: pd.DataFrame, initial_equity_krw: float) -> pd.DataFrame:
    if trades is None or trades.empty:
        return pd.DataFrame()
    data = trades.copy()
    data["signal_grade"] = _series(data, "signal_grade", "REJECT").fillna("REJECT")
    data["target_space_grade"] = _series(data, "target_space_grade", "REJECT").fillna("REJECT")
    data["fractal_state"] = _series(data, "fractal_state", "UNKNOWN").fillna("UNKNOWN")
    data["btc_regime"] = _series(data, "btc_regime", "UNKNOWN").fillna("UNKNOWN")
    data["allocation_pct"] = pd.to_numeric(_series(data, "allocation_pct", 0.0), errors="coerce").fillna(0.0)
    data["position_size_krw"] = pd.to_numeric(_series(data, "position_size_krw", 0.0), errors="coerce").fillna(0.0)
    pnl_source = data["realized_pnl_pct"] if "realized_pnl_pct" in data else _series(data, "net_signal_pnl_pct", 0.0)
    data["trade_pnl_pct"] = pd.to_numeric(pnl_source, errors="coerce").fillna(0.0)
    if "trade_pnl_krw" not in data:
        data["trade_pnl_krw"] = data["position_size_krw"] * data["trade_pnl_pct"] / 100
    data["trade_pnl_krw"] = pd.to_numeric(data["trade_pnl_krw"], errors="coerce").fillna(0.0)
    base_equity = pd.to_numeric(_series(data, "before_equity_krw", initial_equity_krw), errors="coerce")
    data["would_full_seed_pnl_krw"] = base_equity.fillna(initial_equity_krw) * data["trade_pnl_pct"] / 100
    data["would_fixed_10k_pnl_krw"] = 10000 * data["trade_pnl_pct"] / 100
    data["allocation_alpha_krw"] = data["trade_pnl_krw"] - data["would_full_seed_pnl_krw"]
    data["allocation_efficiency"] = data.apply(_efficiency, axis=1)
    data["zone_strength_bucket"] = pd.cut(
        pd.to_numeric(_series(data, "zone_strength", 0), errors="coerce").fillna(0),
        bins=[-1, 40, 60, 80, 101],
        labels=["LOW", "MEDIUM", "HIGH", "ELITE"],
    ).astype(str)
    columns = [
        "signal_grade",
        "target_space_grade",
        "fractal_state",
        "btc_regime",
        "zone_strength_bucket",
        "allocation_pct",
        "position_size_krw",
        "trade_pnl_pct",
        "trade_pnl_krw",
        "would_full_seed_pnl_krw",
        "would_fixed_10k_pnl_krw",
        "allocation_efficiency",
        "allocation_alpha_krw",
    ]
    return data[columns]


def _series(data: pd.DataFrame, column: str, default) -> pd.Series:
    if column in data:
        return data[column]
    return pd.Series([default] * len(data), index=data.index)


def _grade_table(rows: pd.DataFrame) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for grade in GRADE_ORDER:
        part = rows[rows["signal_grade"] == grade]
        wins = part[part["trade_pnl_krw"] > 0]
        losses = part[part["trade_pnl_krw"] < 0]
        gross_profit = float(wins["trade_pnl_krw"].sum())
        gross_loss = abs(float(losses["trade_pnl_krw"].sum()))
        table.append(
            {
                "grade": grade,
                "entry_count": int(len(part)),
                "win_rate": float((part["trade_pnl_krw"] > 0).mean()) if len(part) else 0.0,
                "avg_win_pct": float(wins["trade_pnl_pct"].mean()) if len(wins) else 0.0,
                "avg_loss_pct": float(losses["trade_pnl_pct"].mean()) if len(losses) else 0.0,
                "profit_factor": gross_profit / gross_loss if gross_loss else (999.0 if gross_profit else 0.0),
                "total_pnl_krw": float(part["trade_pnl_krw"].sum()),
                "avg_allocation_pct": float(part["allocation_pct"].mean()) if len(part) else 0.0,
                "full_seed_counterfactual_pnl": float(part["would_full_seed_pnl_krw"].sum()),
                "fixed_10k_counterfactual_pnl": float(part["would_fixed_10k_pnl_krw"].sum()),
                "allocation_alpha_krw": float(part["allocation_alpha_krw"].sum()),
            }
        )
    return table


def _efficiency(row: pd.Series) -> float:
    full = float(row["would_full_seed_pnl_krw"])
    actual = float(row["trade_pnl_krw"])
    if full == 0:
        return 0.0
    return actual / full
