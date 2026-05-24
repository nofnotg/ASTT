from __future__ import annotations


def build_scalp_momentum_exit_plan(mode: str = "TRADABLE_SCALP") -> dict:
    if mode == "TRADABLE_MOMENTUM":
        targets = [0.80, 1.50, None]
        stop = -0.50
        max_hold_seconds = 900
    elif mode == "TRADABLE_SPIKE":
        targets = [1.50, 3.00, None]
        stop = -0.80
        max_hold_seconds = 1800
    else:
        targets = [0.45, 0.80, None]
        stop = -0.35
        max_hold_seconds = 300
    return {
        "mode": mode,
        "exit_plan": [
            {"step": 1, "pct": 0.5, "target_pct": targets[0]},
            {"step": 2, "pct": 0.3, "target_pct": targets[1]},
            {"step": 3, "pct": 0.2, "mode": "TRAILING"},
        ],
        "stop_loss_pct": stop,
        "max_hold_seconds": max_hold_seconds,
        "stop_loss_removable": False,
    }


def manage_scalp_momentum_position(position: dict, snapshot: dict, mode: str = "TRADABLE_SCALP") -> dict:
    plan = build_scalp_momentum_exit_plan(mode)
    pnl_pct = float(snapshot.get("pnl_pct", 0.0) or 0.0)
    hold_seconds = int(snapshot.get("hold_seconds", 0) or 0)
    if pnl_pct <= plan["stop_loss_pct"]:
        return {"decision": "STOP_LOSS", "reason": ["STRUCTURE_OR_PRICE_STOP"], **plan}
    if hold_seconds >= plan["max_hold_seconds"]:
        return {"decision": "TIME_STOP", "reason": ["MAX_HOLD_SECONDS"], **plan}
    if pnl_pct >= plan["exit_plan"][0]["target_pct"]:
        return {"decision": "TAKE_PROFIT", "reason": ["TP1_REACHED"], **plan}
    return {"decision": "HOLD", "reason": [], **plan}
