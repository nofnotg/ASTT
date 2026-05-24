from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from artifact_integrity.production_report_paths import production_docs_reports_dir, production_replay_report_dir
from head_controller.llm_secret_sanitizer import dumps_sanitized
from replay_lab.research.head_controller_evaluation_v557 import run_head_controller_evaluation_v557


class HeadControllerEvaluationHTMLReportV557:
    def build(self, reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> Path:
        result = run_head_controller_evaluation_v557(reports_dir, llm_provider)
        summary = {"schema_version": "1.0", "generated_at": datetime.now().isoformat(), **result}
        html = (
            "<!doctype html><html><head><meta charset='utf-8'><title>Head Controller Evaluation V5.5.7</title></head><body>"
            "<h1>Head Controller Evaluation V5.5.7</h1>"
            "<p>LLM 제안은 검증 후보일 뿐이며 active config 자동 적용은 금지됩니다.</p>"
            f"<pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre></body></html>"
        )
        md = f"# Head Controller Evaluation V5.5.7\n\n- primary_problem: {result.get('primary_problem')}\n- research_score: {result.get('research_score')}\n- auto_apply_allowed: false\n- live_order_allowed: false\n"
        docs = production_docs_reports_dir()
        out = production_replay_report_dir("head_controller_evaluation_v557")
        (docs / "latest_head_controller_evaluation_summary.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (docs / "latest_head_controller_evaluation_report.html").write_text(html, encoding="utf-8")
        (docs / "latest_head_controller_evaluation_report.md").write_text(md, encoding="utf-8")
        (out / "head_controller_evaluation_report.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (out / "head_controller_evaluation_report.html").write_text(html, encoding="utf-8")
        return docs / "latest_head_controller_evaluation_report.html"
