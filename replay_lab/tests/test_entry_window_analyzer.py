from replay_lab.tests.timing_lab_test_helpers import make_clip
from timing_lab.entry_window_analyzer import analyze_clip_entry_windows


def test_entry_window_analyzer_uses_effective_return_and_500k_depth(tmp_path):
    clip = make_clip(tmp_path, [100, 100.4, 101.0])
    result = analyze_clip_entry_windows(clip, initial_cash_krw=500000)
    assert result["entry_windows"]
    assert result["best_window"]["tradable_with_500k"] is True
