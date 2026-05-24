from replay_lab.tests.timing_lab_test_helpers import make_clip
from timing_lab.detector_gap_analyzer import analyze_detector_gaps


def test_detector_gap_analyzer_reports_relaxed_counts(tmp_path):
    make_clip(tmp_path, [100, 101, 100.99])
    result = analyze_detector_gaps(tmp_path)
    assert result["range_touch_detector_status"] in {"THRESHOLD_TOO_STRICT", "DATA_MISSING"}
    assert "recommended_fix" in result
