from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from artifact_integrity.production_report_paths import production_docs_reports_dir, production_replay_report_dir
from head_controller.llm_secret_sanitizer import dumps_sanitized
from replay_lab.research.artifact_integrity_check_v5561 import check_artifact_integrity_v5561


class ArtifactIntegrityHTMLReportV5561:
    def build(self, reports_dir: str | Path = "docs/reports") -> Path:
        result = check_artifact_integrity_v5561(reports_dir)
        summary = {"schema_version": "1.0", "generated_at": datetime.now().isoformat(), **result}
        html = f"<!doctype html><html><body><h1>Artifact Integrity V5.5.6.1</h1><pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre></body></html>"
        md = f"# Artifact Integrity V5.5.6.1\n\n- status: {result['artifact_integrity_status']}\n- stale_or_test_artifact_detected: {result['stale_or_test_artifact_detected']}\n"
        docs = production_docs_reports_dir()
        out = production_replay_report_dir("artifact_integrity_v5561")
        (docs / "latest_artifact_integrity_report.html").write_text(html, encoding="utf-8")
        (docs / "latest_artifact_integrity_report.md").write_text(md, encoding="utf-8")
        (docs / "latest_artifact_integrity_summary.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (out / "artifact_integrity_report.html").write_text(html, encoding="utf-8")
        (out / "artifact_integrity_report.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        return docs / "latest_artifact_integrity_report.html"
