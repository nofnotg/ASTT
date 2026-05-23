from __future__ import annotations

import pandas as pd


def compute_micro_momentum_after_entry(post_entry_seconds, entry_price, max_watch_seconds: int = 30) -> dict:
    frame = post_entry_seconds.copy() if isinstance(post_entry_seconds, pd.DataFrame) else pd.DataFrame(post_entry_seconds or [])
    if frame.empty or not entry_price:
        return {"mfe_3s_pct": 0.0, "mae_3s_pct": 0.0, "mfe_5s_pct": 0.0, "mae_5s_pct": 0.0, "mfe_10s_pct": 0.0, "mae_10s_pct": 0.0, "first_5s_reaction": "FLAT", "micro_failure": True, "micro_success": False, "warnings": ["post_entry_no_data"]}
    frame = frame.head(max_watch_seconds)
    result = {}
    for sec in [3, 5, 10]:
        part = frame.head(sec)
        result[f"mfe_{sec}s_pct"] = (float(part["high"].max()) - entry_price) / entry_price * 100
        result[f"mae_{sec}s_pct"] = (float(part["low"].min()) - entry_price) / entry_price * 100
    if result["mfe_5s_pct"] >= 0.1:
        reaction = "FAVORABLE"
    elif result["mae_5s_pct"] <= -0.25:
        reaction = "ADVERSE"
    else:
        reaction = "FLAT"
    failure = result["mae_5s_pct"] <= -0.25 or result["mfe_10s_pct"] < 0.10
    return {**result, "first_5s_reaction": reaction, "micro_failure": bool(failure), "micro_success": bool(result["mfe_10s_pct"] >= 0.2), "warnings": []}
