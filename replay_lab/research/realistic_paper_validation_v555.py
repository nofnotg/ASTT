from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


def validate_realistic_paper_v555(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555") -> dict:
    sessions = _sessions(sessions_dir)
    trade_count = sum(s.get("trade_count", 0) for s in sessions)
    wins = sum(s.get("win_rate", 0) * s.get("trade_count", 0) for s in sessions)
    total_pnl = sum(s.get("total_pnl_krw", 0.0) for s in sessions)
    result = {"session_count": len(sessions), "duration_minutes": sum(s.get("duration_minutes", 0) for s in sessions), "candidate_count": sum(s.get("candidate_count", 0) for s in sessions), "enter_count": sum(s.get("enter_count", 0) for s in sessions), "enter_rate": 0.0, "trade_count": trade_count, "win_rate": wins / trade_count if trade_count else 0.0, "profit_factor": _pf(sessions), "expectancy_pct": _avg([s.get("expectancy_pct") for s in sessions if s.get("expectancy_pct") is not None]), "total_pnl_krw": total_pnl, "total_return_pct": _avg([s.get("total_return_pct", 0.0) for s in sessions]), "max_drawdown_pct": min([s.get("max_drawdown_pct", 0.0) for s in sessions], default=0.0), "avg_hold_seconds": _avg([s.get("avg_hold_seconds", 0.0) for s in sessions]), "fee_total_krw": sum(s.get("fee_total_krw", 0.0) for s in sessions), "slippage_estimated_krw": sum(s.get("slippage_estimated_krw", 0.0) for s in sessions), "micro_failure_exit_count": 0, "time_stop_count": trade_count, "take_profit_count": 0, "stop_loss_count": 0, "live_readiness": "LIVE_NOT_ALLOWED", "sessions": sessions}
    result["enter_rate"] = result["enter_count"] / result["candidate_count"] if result["candidate_count"] else 0.0
    out = REPLAY_STORE_DIR / "reports" / "realistic_paper_v555"
    out.mkdir(parents=True, exist_ok=True)
    (out / "realistic_paper_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def _sessions(root) -> list[dict]:
    root = Path(root)
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.glob("*/session_summary.json"))]


def _avg(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _pf(sessions):
    # Session summaries store net totals only; detailed trade aggregation is in ledger files.
    pnl = [s.get("total_pnl_krw", 0.0) for s in sessions if s.get("trade_count", 0)]
    wins = sum(x for x in pnl if x > 0)
    losses = abs(sum(x for x in pnl if x < 0))
    return wins / losses if losses else (999.0 if wins else 0.0)
