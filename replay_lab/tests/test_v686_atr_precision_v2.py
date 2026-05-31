from __future__ import annotations

from atr_precision_v2.atr_precision_v2_report_builder import final_atr_decision


def test_v686_atr_precision_requires_80_pct_ltf_coverage() -> None:
    decision = final_atr_decision({"best_coverage_pct": 79.9}, {"return_pct": 999.0, "mdd_pct": 0.0}, {"return_pct": 1.0, "mdd_pct": -10.0})
    assert decision == "ATR_DATA_INSUFFICIENT"


def test_v686_atr_precision_can_only_be_shadow_candidate_after_coverage() -> None:
    decision = final_atr_decision({"best_coverage_pct": 85.0}, {"return_pct": 10.0, "mdd_pct": -4.0, "lookahead_fail_count": 0}, {"return_pct": 5.0, "mdd_pct": -8.0})
    assert decision == "ATR_VALIDATED_SHADOW_CANDIDATE"
