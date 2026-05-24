from replay_lab.tests.timing_lab_test_helpers import make_clip
from timing_lab.timing_labeler import label_clip


def test_timing_labeler_labels_entry_window_and_fake_signal(tmp_path):
    assert label_clip(make_clip(tmp_path / "a", [100, 100.4, 101]))["label"] == "ENTRY_WINDOW"
    assert label_clip(make_clip(tmp_path / "b", [100, 100.01, 100.02]))["label"] in {"FAKE_SIGNAL", "TOO_LATE", "SPREAD_TRAP"}
