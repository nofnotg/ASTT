from __future__ import annotations

from replay_lab.feedback.fake_signal_decomposition_html_report_v5r2 import _read, _write


class HeadControllerV5R2ReviewHTMLReport:
    def build(self, output_dir="docs/reports") -> dict:
        sections = [
            "Head Controller Summary",
            "Primary Problem",
            "Project Decision",
            "Scorecard Score",
            "Recommended Event Types",
            "Event Types To Pause",
            "Calibration Recommendations",
            "Next Experiments",
            "Risk Flags",
            "Config Proposals",
            "Auto Apply Disabled",
            "Live Order Disabled",
        ]
        return _write(output_dir, "latest_head_controller_v5r2_review", "ASTT V5.R2 Head Controller Review", _read("replay_store/project_scorecard/head_controller_v5r2_review.json"), sections)
