from __future__ import annotations

from btcd.btcd_regime_detector import build_bear_composite, detect_global_btcd_regime


def test_btcd_regime_detector_marks_rising_and_bear_defense():
    assert detect_global_btcd_regime(1.2, 2.5, 0.4) == "BTCD_RISING"
    composite = build_bear_composite("BTCD_RISING", "BTC_FLOW_SPIKE", 0.2, 0.7, -12.0, -4.0)
    assert composite.bear_transition_score >= 60
    assert composite.bear_state in {"BEAR_DEFENSE", "BEAR_BOUNCE_ONLY", "LOCKDOWN"}

