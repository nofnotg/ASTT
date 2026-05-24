from capital.signal_strength_sizer import size_signal_strength


def test_signal_strength_sizer_wait_is_c_grade_no_allocation():
    result = size_signal_strength({"entry_decision": "WAIT", "micro_strength_score": 90}, {"initial_cash_krw": 500000})
    assert result["signal_grade"] == "C"
    assert result["allocation_krw"] == 0
