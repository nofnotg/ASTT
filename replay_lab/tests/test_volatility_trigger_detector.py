from live_capture.volatility_trigger_detector import detect_btc_shock, detect_volume_spike


def test_volatility_triggers():
    assert detect_btc_shock(0.4)["triggered"] is True
    assert detect_volume_spike(300, 100)["triggered"] is True
