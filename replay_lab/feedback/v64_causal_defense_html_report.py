from __future__ import annotations

from replay_lab.feedback.v64_common_html import build_v64_html_report


class V64CausalDefenseHTMLReport:
    def build(self, reports_dir: str = "docs/reports") -> dict[str, str]:
        return build_v64_html_report("ASTT V6.4 Causal Defense Re-run", f"{reports_dir}/latest_v64_causal_defense_summary.json", f"{reports_dir}/latest_v64_causal_defense_report.html", "처음 거래부터 거래 직전 정보만으로 방어를 켰을 때의 결과입니다.")
