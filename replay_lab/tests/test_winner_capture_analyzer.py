from winner_mining.winner_capture_analyzer import classify_capture


def test_capture_classifications():
    winner = 100_000
    assert classify_capture(90_000, winner) == "TIMELY_CAPTURE"
    assert classify_capture(10_000, winner) == "EARLY_CAPTURE"
    assert classify_capture(110_000, winner) == "LATE_CAPTURE"
    assert classify_capture(None, winner) == "MISSED"
