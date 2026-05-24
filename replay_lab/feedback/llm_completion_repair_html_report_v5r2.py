from __future__ import annotations

from replay_lab.feedback.fake_signal_decomposition_html_report_v5r2 import _read, _write


class LLMCompletionRepairHTMLReportV5R2:
    def build(self, output_dir="docs/reports") -> dict:
        return _write(output_dir, "latest_llm_completion_repair", "ASTT V5.R2 LLM Completion Repair", _read("docs/reports/latest_llm_completion_repair_summary.json"), ["V5.R1 LLM fallback 臾몄젣", "minimum completion test 寃곌낵", "prompt tokens", "completion tokens", "total tokens", "schema valid ?щ?", "fallback ?щ?", "estimated cost", "token budget ?곹깭"])
