from risk.risk_position_sizer import size_position


def test_risk_position_sizer_uses_stop_distance():
    result = size_position(500000, 10000, 9700, risk_per_trade_pct=1.0)
    assert 160000 <= result["position_krw"] <= 170000
    assert result["sizing_valid"] is True
