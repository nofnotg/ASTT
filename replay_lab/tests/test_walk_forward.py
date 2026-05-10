from replay_lab.replay.walk_forward import build_walk_forward_windows


def test_walk_forward_windows_are_separated():
    windows = build_walk_forward_windows(90)
    assert windows[0]["train_end"] < windows[0]["test_start"]
    assert windows[-1]["test_end"] == 90

