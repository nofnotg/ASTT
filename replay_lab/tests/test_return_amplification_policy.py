from __future__ import annotations

from portfolio.return_amplification_policy import is_amplifiable_trade


def test_only_high_quality_ict_or_combined_trades_can_be_amplified():
    assert is_amplifiable_trade({"strategy": "COMBINED_VOLUME_ICT", "setup_type": "FVG_OB_OVERLAP", "plan": "PLAN_B_COMBINED_CONTEXT", "regime": "ALT_ROTATION"})
    assert not is_amplifiable_trade({"strategy": "DADDY_VOLUME_NECKLINE", "setup_type": "FIB_PULLBACK_VOLUME", "plan": "PLAN_B_COMBINED_CONTEXT", "regime": "ALT_ROTATION"})
    assert not is_amplifiable_trade({"strategy": "COMBINED_VOLUME_ICT", "setup_type": "FVG_OB_OVERLAP", "plan": "PLAN_B_COMBINED_CONTEXT", "regime": "CHOP"})
