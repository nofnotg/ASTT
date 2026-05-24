from timing_lab.timing_state_machine import EntryTimingStateMachine


def test_timing_state_machine_transitions_to_enter_and_abort():
    event = {"market": "KRW-TEST", "event_id": "e1", "event_time_ms": 1}
    good = {"spread_stable": True, "depth_sufficient": True, "buy_trade_ratio": 0.7, "volume_burst": True, "follow_through": True, "entry_window_exists": True, "allocator_grade": "B"}
    assert EntryTimingStateMachine().apply(event, good).state == "ENTER"
    bad = {"spread_stable": False, "depth_sufficient": True}
    assert EntryTimingStateMachine().apply(event, bad).state == "ABORT"
