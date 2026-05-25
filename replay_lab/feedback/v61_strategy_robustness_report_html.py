from __future__ import annotations

from replay_lab.feedback.v6_report_common import build_json_html_report


class V61StrategyRobustnessReportHTML:
    def build(self, output_dir: str = "docs/reports") -> dict[str, str]:
        return build_json_html_report("latest_v61_strategy_robustness_summary.json", "latest_v61_strategy_robustness_report.html", "V6.1 Strategy Robustness", output_dir)
