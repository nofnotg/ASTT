from timing_lab.project_kill_criteria import decide_project


def test_project_kill_criteria_continue_pause_kill():
    assert decide_project(70, 1, 1, 1)["project_decision"] == "CONTINUE"
    assert decide_project(40, 0, 0, 0)["project_decision"] == "PAUSE"
    assert decide_project(20, 0, 0, 0)["project_decision"] == "KILL_RECOMMENDED"
