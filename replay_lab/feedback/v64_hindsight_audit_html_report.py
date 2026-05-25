from __future__ import annotations

from replay_lab.feedback.v64_common_html import build_v64_html_report


class V64HindsightAuditHTMLReport:
    def build(self, reports_dir: str = "docs/reports") -> dict[str, str]:
        return build_v64_html_report("ASTT V6.4 Hindsight Audit", f"{reports_dir}/latest_v64_hindsight_audit_summary.json", f"{reports_dir}/latest_v64_hindsight_audit_report.html", "방어 판단이 정답지를 보지 않았는지 검사합니다.")
