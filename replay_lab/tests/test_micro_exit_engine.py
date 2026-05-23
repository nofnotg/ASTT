from execution.micro_exit_engine import decide_micro_exit


def test_micro_exit_engine_take_profit_and_stop():
    ctx = {"entry_price": 100, "target_price": 101, "stop_price": 99, "max_hold_seconds": 120}

    assert decide_micro_exit(ctx, {}, {"close": 101.2}, elapsed_seconds=3)["exit_decision"] == "TAKE_PROFIT"
    assert decide_micro_exit(ctx, {}, {"close": 98.8}, elapsed_seconds=3)["exit_decision"] == "STOP_LOSS"


def test_micro_exit_engine_micro_failure_and_time_stop():
    ctx = {"entry_price": 100, "target_price": 101, "stop_price": 99, "max_hold_seconds": 5}

    assert decide_micro_exit(ctx, {"micro_failure": True}, {"close": 99.8}, elapsed_seconds=3)["exit_decision"] == "MICRO_FAILURE_EXIT"
    assert decide_micro_exit(ctx, {"micro_failure": False}, {"close": 100.1}, elapsed_seconds=5)["exit_decision"] == "TIME_STOP"
