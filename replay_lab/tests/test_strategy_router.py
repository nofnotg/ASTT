from __future__ import annotations

from strategy_router.strategy_router import plan_for_trade


def test_strategy_router_routes_ict_sweep_to_plan_a():
    route = plan_for_trade({"strategy": "ICT_FVG_OB_SWEEP", "setup_type": "FVG_LIQUIDITY_SWEEP"})
    assert route["plan"] == "PLAN_A_ICT_FAT_TAIL"
