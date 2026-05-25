from __future__ import annotations

from analysis.v66_btcd_signal_effect_analyzer import signal_decision


def test_v66_signal_decision_keeps_negative_as_warning():
    assert signal_decision(-1) == "KEEP_AS_SOFT_WARNING"
    assert signal_decision(1) == "DO_NOT_HARD_BLOCK"

