from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def summarize_frames(frames: dict[str, pd.DataFrame]) -> dict:
    decisions = frames.get("decisions", pd.DataFrame())
    trades = frames.get("paper_trades", pd.DataFrame())
    entries = len(trades)
    wins = int((trades.get("pnl_pct", pd.Series(dtype=float)) > 0).sum()) if not trades.empty else 0
    total_pnl = float(trades.get("pnl_pct", pd.Series(dtype=float)).sum()) if not trades.empty else 0.0
    return {
        "sessions": int(len(frames.get("session_results", pd.DataFrame()))),
        "decisions": int(len(decisions)),
        "entries": entries,
        "wins": wins,
        "win_rate": wins / entries if entries else 0.0,
        "total_pnl_pct": total_pnl,
        "veto_count": int((decisions.get("vetoed", pd.Series(dtype=bool)) == True).sum()) if not decisions.empty else 0,
    }


def write_replay_report(exp_dir: Path, experiment_id: str, frames: dict[str, pd.DataFrame]) -> Path:
    metrics = summarize_frames(frames)
    (exp_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    report = exp_dir / "report.md"
    report.write_text(
        f"""# Replay Lab Report - {experiment_id}

## Summary
- sessions: {metrics['sessions']}
- decisions: {metrics['decisions']}
- entries: {metrics['entries']}
- wins: {metrics['wins']}
- win_rate: {metrics['win_rate']:.2%}
- total_pnl_pct: {metrics['total_pnl_pct']:.2f}
- iris_veto_count: {metrics['veto_count']}

## Safety Notes
- Replay uses cached/public historical data only.
- Replay results are research artifacts and are not applied to LIVE settings.
- APPROVED exports are required before the main app can import any candidate.
""",
        encoding="utf-8",
    )
    return report

