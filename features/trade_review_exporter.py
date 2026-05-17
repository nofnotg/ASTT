from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


REVIEW_COLUMNS = [
    "date",
    "market",
    "strategy_id",
    "entry_time",
    "entry_price",
    "stop_price",
    "target_price",
    "exit_time",
    "exit_price",
    "realized_pnl_pct",
    "exit_reason",
    "daily_state",
    "h4_state",
    "zone_used",
    "zone_low",
    "zone_high",
    "zone_quality_score",
    "target_space_pct",
    "risk_reward",
    "btc_regime",
    "entry_reason",
    "invalid_reason",
    "actual_path_summary",
    "win_loss_reason",
    "review_question",
]


def build_trade_review_rows(trades: pd.DataFrame) -> list[dict]:
    rows = []
    for trade in trades.to_dict("records"):
        pnl = float(trade.get("realized_pnl_pct", 0.0))
        rows.append(
            {
                "date": trade.get("date_kst", ""),
                "market": trade.get("market", ""),
                "strategy_id": trade.get("strategy_id", ""),
                "entry_time": trade.get("entry_time_kst", ""),
                "entry_price": trade.get("entry_price", 0.0),
                "stop_price": trade.get("stop_price", trade.get("zone_stop", 0.0)),
                "target_price": trade.get("target_price", trade.get("target_1", 0.0)),
                "exit_time": trade.get("exit_time_kst", ""),
                "exit_price": trade.get("exit_price", 0.0),
                "realized_pnl_pct": pnl,
                "exit_reason": trade.get("exit_reason", ""),
                "daily_state": trade.get("daily_state", ""),
                "h4_state": trade.get("h4_state", ""),
                "zone_used": bool(trade.get("zone_used", False)),
                "zone_low": trade.get("zone_low", trade.get("zone_stop", 0.0)),
                "zone_high": trade.get("zone_high", trade.get("entry_price", 0.0)),
                "zone_quality_score": trade.get("zone_quality_score", 0.0),
                "target_space_pct": trade.get("target_space_pct", 0.0),
                "risk_reward": trade.get("risk_reward", trade.get("risk_reward_1", 0.0)),
                "btc_regime": trade.get("btc_regime", ""),
                "entry_reason": trade.get("entry_reason", ""),
                "invalid_reason": trade.get("invalid_reason", ""),
                "actual_path_summary": actual_path_summary(trade),
                "win_loss_reason": "target_or_positive_exit" if pnl > 0 else "stop_or_negative_exit",
                "review_question": review_question(trade),
            }
        )
    return rows


def actual_path_summary(trade: dict) -> str:
    return f"MFE {float(trade.get('mfe_pct', 0.0)):.2f}%, MAE {float(trade.get('mae_pct', 0.0)):.2f}%, result {float(trade.get('realized_pnl_pct', 0.0)):.2f}%"


def review_question(trade: dict) -> str:
    if float(trade.get("realized_pnl_pct", 0.0)) < 0:
        return "Was the entry late, was the stop too close, or was the zone visually weak?"
    return "Was the winning move caused by MTF structure, zone reaction, or a broad market move?"


def export_trade_review(rows: list[dict], markdown_path: Path, csv_path: Path) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows([{col: row.get(col, "") for col in REVIEW_COLUMNS} for row in rows])
    lines = ["# ASTT V5.4 Trade Review", ""]
    for row in rows:
        lines.append(f"## {row.get('date')} {row.get('market')} {row.get('strategy_id')}")
        lines.append(f"- PnL: {float(row.get('realized_pnl_pct', 0.0)):.2f}% / {row.get('exit_reason')}")
        lines.append(f"- Path: {row.get('actual_path_summary')}")
        lines.append(f"- Question: {row.get('review_question')}")
        lines.append("")
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
