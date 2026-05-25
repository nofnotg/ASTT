from __future__ import annotations

from analysis.top_trade_contribution import top_win_contribution
from analysis.winner_removal_stress_test import remove_top_winners


def analyze_big_win_dependency(strategy: str, trades: list[dict], initial_cash_krw: float = 500000) -> dict:
    without_1 = remove_top_winners(trades, 1, initial_cash_krw)
    without_3 = remove_top_winners(trades, 3, initial_cash_krw)
    without_5 = remove_top_winners(trades, 5, initial_cash_krw)
    decision = "FAT_TAIL_ACCEPTABLE"
    if without_3["total_return_pct"] < -5:
        decision = "FAT_TAIL_FRAGILE"
    if top_win_contribution(trades, 1) > 120:
        decision = "RANDOM_SPIKE_SUSPECTED"
    return {
        "strategy": strategy,
        "top_1_win_contribution_pct": top_win_contribution(trades, 1),
        "top_3_win_contribution_pct": top_win_contribution(trades, 3),
        "top_5_win_contribution_pct": top_win_contribution(trades, 5),
        "return_without_top_1": without_1["total_return_pct"],
        "return_without_top_3": without_3["total_return_pct"],
        "return_without_top_5": without_5["total_return_pct"],
        "profit_factor_without_top_1": without_1["profit_factor"],
        "profit_factor_without_top_3": without_3["profit_factor"],
        "dependency_decision": decision,
    }
