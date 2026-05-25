from __future__ import annotations


def run_risk_parameter_sweep_rows(strategy_summaries: list[dict]) -> list[dict]:
    rows = []
    for summary in strategy_summaries:
        base_return = float(summary.get("total_return_pct", 0.0))
        base_mdd = float(summary.get("max_drawdown_pct", 0.0))
        for risk in [0.5, 1.0, 1.5, 2.0]:
            for rr in [1.2, 1.5, 1.8, 2.5, 3.0]:
                scaled = base_return * risk
                mdd = base_mdd * risk
                decision = "KEEP" if scaled > 0 and mdd > -8 else "REJECT"
                rows.append({
                    "strategy": summary["strategy"],
                    "risk_pct": risk,
                    "rr": rr,
                    "hold": "setup-based exit",
                    "trades": summary.get("trade_count", 0),
                    "return_pct": scaled,
                    "profit_factor": summary.get("profit_factor"),
                    "mdd_pct": mdd,
                    "decision": decision,
                })
    return rows
