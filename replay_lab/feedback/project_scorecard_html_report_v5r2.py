from __future__ import annotations

from replay_lab.feedback.fake_signal_decomposition_html_report_v5r2 import _read, _write


class ProjectScorecardHTMLReportV5R2:
    def build(self, output_dir="docs/reports") -> dict:
        return _write(output_dir, "latest_project_scorecard", "ASTT V5.R2 Project Scorecard", _read("replay_store/project_scorecard/project_scorecard_v5r2.json"), ["?꾨줈?앺듃 ?앹〈 ?먯닔", "??ぉ蹂??먯닔", "CONTINUE / PAUSE / KILL_RECOMMENDED ?먯젙", "?먯젙 洹쇨굅", "?ㅼ쓬 1???ㅽ뿕 ?꾩슂 ?щ?", "?먭린 議곌굔"])
