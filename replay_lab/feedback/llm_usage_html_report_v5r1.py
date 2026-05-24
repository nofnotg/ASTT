from __future__ import annotations

import json
from pathlib import Path

from replay_lab.research.llm_usage_audit_v5r1 import audit_llm_usage_v5r1


class LLMUsageHTMLReportV5R1:
    def build(self, output_dir: str | Path = "docs/reports") -> dict:
        summary = audit_llm_usage_v5r1(output_dir)
        sections = [
            "Total LLM Calls",
            "Total Prompt Tokens",
            "Total Completion Tokens",
            "Total Tokens",
            "Estimated Cost",
            "Tokens By Purpose",
            "Tokens By Model",
            "Fallback Count",
            "Schema Fail Count",
            "Unsafe Proposal Count",
            "Token Budget Status",
        ]
        return _write(output_dir, "latest_llm_usage", "ASTT V5.R1 LLM Usage Report", summary, sections)


def _write(output_dir: str | Path, stem: str, title: str, summary: dict, sections: list[str]) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{stem}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md = "# " + title + "\n\n" + "\n".join(f"## {s}\n\n```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```\n" for s in sections)
    (out / f"{stem}_report.md").write_text(md, encoding="utf-8")
    html = "".join(f"<h2>{s}</h2><pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre>" for s in sections)
    (out / f"{stem}_report.html").write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head><body><h1>{title}</h1>{html}</body></html>", encoding="utf-8")
    return summary
