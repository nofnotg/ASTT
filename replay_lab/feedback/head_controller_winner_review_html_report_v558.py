from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from artifact_integrity.production_report_paths import production_docs_reports_dir, production_replay_report_dir
from head_controller.llm_secret_sanitizer import dumps_sanitized
from replay_lab.research.head_controller_winner_pattern_review_v558 import run_head_controller_winner_review_v558


class HeadControllerWinnerReviewHTMLReportV558:
    def build(self, reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> Path:
        result = run_head_controller_winner_review_v558(reports_dir, llm_provider)
        summary = {"schema_version": "1.0", "generated_at": datetime.now().isoformat(), **result}
        html = f"<!doctype html><html><head><meta charset='utf-8'><title>Head Controller Winner Review V5.5.8</title></head><body><h1>Head Controller Winner Review V5.5.8</h1><p>Head Controller 제안은 검증 후보일 뿐입니다. 자동 적용 금지.</p><pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre></body></html>"
        md = f"# Head Controller Winner Review V5.5.8\n\n- primary_problem: {result.get('primary_problem')}\n- auto_apply_allowed: false\n- live_order_allowed: false\n"
        docs = production_docs_reports_dir()
        out = production_replay_report_dir("head_controller_winner_review_v558")
        (docs / "latest_head_controller_winner_review_summary.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (docs / "latest_head_controller_winner_review_report.html").write_text(html, encoding="utf-8")
        (docs / "latest_head_controller_winner_review_report.md").write_text(md, encoding="utf-8")
        (out / "head_controller_winner_review_report.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (out / "head_controller_winner_review_report.html").write_text(html, encoding="utf-8")
        return docs / "latest_head_controller_winner_review_report.html"
