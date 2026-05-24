from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from capital.capital_policy import default_capital_policy, validate_capital_policy
from capital.entry_ladder import build_entry_ladder
from capital.exit_ladder import build_exit_ladder
from capital.full_seed_allocator import allocate_full_seed
from execution.account_equity_tracker import AccountEquityTracker
from execution.ladder_position_manager import validate_ladder_position_plan
from replay_lab.paths import REPLAY_STORE_DIR


def run_full_seed_paper_session_v557(
    duration_minutes: int = 60,
    initial_cash_krw: float = 500000,
    sizing_mode: str = "FULL_SEED_LADDER",
    strategies: list[str] | None = None,
    scenario: str = "realistic_1",
    research_mode: bool = True,
) -> dict:
    policy = validate_capital_policy({**default_capital_policy(initial_cash_krw), "research_mode": research_mode})
    entry = _load_entry_discovery()
    candidate_count = int(entry.get("candidate_count", 0))
    strict = _profile(entry, "STRICT")
    balanced = _profile(entry, "BALANCED")
    enter_count = int((balanced or strict or {}).get("enter", 0))
    trade_count = 0 if enter_count == 0 else enter_count
    tracker = AccountEquityTracker(initial_cash_krw)
    tracker.add(initial_cash_krw, 1)
    candidate = {"entry_decision": "WAIT" if enter_count == 0 else "ENTER", "micro_strength_score": 0, "research_only": enter_count == 0}
    allocation = allocate_full_seed(candidate, policy)
    entry_ladder = build_entry_ladder(allocation["allocation_krw"] if sizing_mode == "FULL_SEED_LADDER" else initial_cash_krw)
    exit_ladder = build_exit_ladder()
    ladder_validation = validate_ladder_position_plan(entry_ladder, exit_ladder)
    summary = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "session_id": datetime.now().strftime("full_seed_v557_%Y%m%d_%H%M%S"),
        "duration_minutes": duration_minutes,
        "strategies": strategies or ["MICRO_ACCELERATION", "VWAP_RECLAIM", "EMA_PULLBACK", "ORDERBOOK_IMBALANCE"],
        "scenario": scenario,
        "initial_cash_krw": float(initial_cash_krw),
        "final_equity_krw": float(initial_cash_krw),
        "total_pnl_krw": 0.0,
        "total_return_pct": 0.0,
        "candidate_count": candidate_count,
        "enter_count": enter_count,
        "trade_count": trade_count,
        "win_rate": None if trade_count == 0 else 0.0,
        "profit_factor": None if trade_count == 0 else 0.0,
        "expectancy_pct": None if trade_count == 0 else 0.0,
        "max_drawdown_pct": tracker.max_drawdown_pct,
        "fee_total_krw": 0.0,
        "slippage_estimated_krw": 0.0,
        "default_sizing_mode": "FULL_SEED_LADDER",
        "sizing_mode": sizing_mode,
        "research_mode": True,
        "real_order_enabled": False,
        "pnl_evaluable": trade_count > 0,
        "primary_problem": "ENTER_0" if trade_count == 0 else "PAPER_TRADES_AVAILABLE",
        "capital_policy": policy,
        "signal_strength_counts": {"C": candidate_count, "B": 0, "A": 0, "S": 0},
        "entry_ladder": entry_ladder,
        "exit_ladder": exit_ladder,
        "ladder_validation": ladder_validation,
        "equity_curve": tracker.curve,
        "live_readiness": "LIVE_NOT_ALLOWED",
    }
    session_dir = REPLAY_STORE_DIR / "sessions" / "full_seed_v557" / summary["session_id"]
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "session_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    out = REPLAY_STORE_DIR / "reports" / "full_seed_allocator_v557"
    out.mkdir(parents=True, exist_ok=True)
    (out / "full_seed_session.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return summary


def _load_entry_discovery() -> dict:
    path = Path("docs/reports/latest_entry_discovery_summary.json")
    if not path.exists():
        return {"candidate_count": 0, "profiles": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _profile(summary: dict, name: str) -> dict | None:
    return next((row for row in summary.get("profiles", []) if row.get("profile") == name), None)
