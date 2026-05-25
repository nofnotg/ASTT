from __future__ import annotations

from replay_lab.feedback.v62_investor_html_common import read_json, write_investor_html


class V62StrategyRouterReportHTML:
    def build(self, output_dir: str = "docs/reports") -> dict[str, str]:
        payload = read_json(f"{output_dir}/latest_v62_strategy_router_summary.json")
        return write_investor_html("V6.2 Strategy Router Report", payload, f"{output_dir}/latest_v62_strategy_router_report.html", payload.get("router_rows", []))
