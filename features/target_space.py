from __future__ import annotations


def compute_target_space(entry_price: float, stop_price: float, zones_above: list[dict], zones_below: list[dict], trend_context: dict) -> dict:
    risk_pct = (entry_price - stop_price) / entry_price * 100 if entry_price else 0.0
    above = sorted([z for z in zones_above if float(z.get("zone_high", 0)) > entry_price], key=lambda z: z.get("zone_low", 0))
    t1 = float(above[0]["zone_low"]) if above else entry_price * 1.012
    t2 = float(above[0]["zone_high"]) if above else entry_price * 1.025
    t3 = float(above[1]["zone_high"]) if len(above) > 1 else entry_price * 1.04
    t1_pct = (t1 - entry_price) / entry_price * 100 if entry_price else 0.0
    t2_pct = (t2 - entry_price) / entry_price * 100 if entry_price else 0.0
    t3_pct = (t3 - entry_price) / entry_price * 100 if entry_price else 0.0
    rr1 = t1_pct / risk_pct if risk_pct else 0.0
    rr2 = t2_pct / risk_pct if risk_pct else 0.0
    rr3 = t3_pct / risk_pct if risk_pct else 0.0
    max_space = max(t1_pct, t2_pct, t3_pct)
    if t1_pct < 0.8 or rr1 < 1.0:
        grade = "REJECT"
    elif t1_pct < 1.5:
        grade = "C"
    elif t1_pct < 3.0:
        grade = "B"
    elif t2_pct < 6.0:
        grade = "A"
    else:
        grade = "A_PLUS"
    return {"entry_price": entry_price, "stop_price": stop_price, "risk_pct": risk_pct, "target_1": t1, "target_1_pct": t1_pct, "target_2": t2, "target_2_pct": t2_pct, "target_3": t3, "target_3_pct": t3_pct, "max_target_space_pct": max_space, "risk_reward_1": rr1, "risk_reward_2": rr2, "risk_reward_3": rr3, "target_space_grade": grade, "warnings": []}
