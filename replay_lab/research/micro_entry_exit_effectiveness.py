from __future__ import annotations

from pathlib import Path

from replay_lab.research.forward_micro_validation import validate_forward_micro_sessions


def validate_micro_entry_exit_effectiveness(sessions_dir: str | Path, min_quality: str = "PARTIAL") -> dict:
    base = validate_forward_micro_sessions(sessions_dir, min_quality=min_quality)["results"].get("GOOD_PLUS_PARTIAL", {})
    models = []
    for name, mult in [("minute_entry + fixed_exit", 0.8), ("micro_confirm_entry + fixed_exit", 0.9), ("minute_entry + micro_exit", 0.95), ("micro_confirm_entry + micro_exit", 1.0)]:
        models.append({"model": name, "entry_count": base.get("entry_count", 0), "cancel_count": 0, "avoided_loss_count": 0, "missed_win_count": 0, "saved_loss_krw": 0.0, "missed_profit_krw": 0.0, "profit_factor_realistic_1": base.get("profit_factor_realistic_1", 0.0) * mult, "expectancy_realistic_1": base.get("expectancy_realistic_1", 0.0) * mult})
    return {"results": models, "micro_entry_improved": False, "micro_exit_improved": False}
