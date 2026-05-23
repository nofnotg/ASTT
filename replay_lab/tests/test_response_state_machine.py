from execution.response_state_machine import ResponseStateMachine


def test_response_state_machine_transitions():
    machine = ResponseStateMachine()
    machine.on_setup()
    machine.arm_or_idle(True, "risk_pass")
    machine.enter()
    machine.manage()
    machine.exit("TAKE_PROFIT")
    machine.review()

    assert [row["state"] for row in machine.history] == ["SETUP_FOUND", "ARMED", "ENTERED", "MANAGE", "EXIT", "REVIEW"]


def test_response_state_machine_veto_returns_idle():
    machine = ResponseStateMachine()
    machine.on_setup()
    machine.arm_or_idle(False, "spread_too_wide")

    assert machine.state == "IDLE"
