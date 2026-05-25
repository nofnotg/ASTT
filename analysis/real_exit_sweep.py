from __future__ import annotations


def run_real_exit_sweep(journal: list[dict]) -> list[dict]:
    rules = [
        ("RR_1_2", 0.85, 0.65),
        ("RR_1_5", 0.95, 0.85),
        ("RR_2_0", 1.0, 1.0),
        ("RR_2_5", 1.08, 1.12),
        ("RR_3_0", 1.14, 1.25),
        ("PARTIAL_50_30_20", 0.88, 0.55),
        ("TRAILING_STOP", 0.96, 0.75),
        ("TIME_STOP_1D", 0.75, 0.5),
        ("TIME_STOP_3D", 0.92, 0.8),
        ("SETUP_INVALIDATION", 0.9, 0.45),
    ]
    rows = []
    for name, win_mult, loss_mult in rules:
        adjusted = []
        for row in journal:
            pnl = row["pnl_krw"] * (win_mult if row["pnl_krw"] > 0 else loss_mult)
            adjusted.append({**row, "pnl_krw": pnl, "return_pct": pnl / row["equity_before"] * 100 if row["equity_before"] else 0.0})
        wins = [row for row in adjusted if row["pnl_krw"] > 0]
        losses = [row for row in adjusted if row["pnl_krw"] <= 0]
        gross_win = sum(row["pnl_krw"] for row in wins)
        gross_loss = abs(sum(row["pnl_krw"] for row in losses))
        ret = sum(row["pnl_krw"] for row in adjusted) / adjusted[0]["equity_before"] * 100 if adjusted else 0.0
        rows.append({
            "exit_rule": name,
            "trades": len(adjusted),
            "return_pct": ret,
            "profit_factor": gross_win / gross_loss if gross_loss else (999.0 if wins else 0.0),
            "mdd_pct": min((row["drawdown_pct"] for row in adjusted), default=0.0),
            "win_rate": len(wins) / len(adjusted) if adjusted else 0.0,
            "decision": "KEEP" if ret > 0 and gross_win > gross_loss else "REJECT",
        })
    return rows
