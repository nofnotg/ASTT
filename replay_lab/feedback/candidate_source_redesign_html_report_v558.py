from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from artifact_integrity.production_report_paths import production_docs_reports_dir, production_replay_report_dir
from head_controller.llm_secret_sanitizer import dumps_sanitized


class CandidateSourceRedesignHTMLReportV558:
    def build(self) -> Path:
        capture = _read("replay_store/winner_mining/reports/winner_capture_rate.json")
        missed = _read("replay_store/winner_mining/reports/missed_winner_analysis.json")
        patterns = _read("replay_store/winner_mining/reports/winner_patterns.json")
        validation = _read("replay_store/winner_mining/reports/redesigned_candidate_source_validation.json")
        full_seed = _read("replay_store/winner_mining/reports/full_seed_winner_candidate_validation.json")
        summary = {
            "schema_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "capture_rate": capture,
            "missed_winner_analysis": missed,
            "winner_patterns": patterns,
            "redesigned_source_validation": validation.get("source_validation", []),
            "full_seed_connection": full_seed,
            "live_readiness": "LIVE_NOT_ALLOWED",
            "research_mode": True,
            "real_order_enabled": False,
        }
        html = f"<!doctype html><html><head><meta charset='utf-8'><title>Candidate Source Redesign V5.5.8</title></head><body><h1>Candidate Source Redesign V5.5.8</h1><p>새 source는 검증 후보이며 active config가 아닙니다.</p><pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre></body></html>"
        md = f"# Candidate Source Redesign V5.5.8\n\n- redesigned_candidate_count: {validation.get('candidate_count', 0)}\n- grade_b_plus_count: {validation.get('grade_b_plus_count', 0)}\n"
        docs = production_docs_reports_dir()
        out = production_replay_report_dir("candidate_source_redesign_v558")
        (docs / "latest_candidate_source_redesign_summary.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (docs / "latest_candidate_source_redesign_report.html").write_text(html, encoding="utf-8")
        (docs / "latest_candidate_source_redesign_report.md").write_text(md, encoding="utf-8")
        (out / "candidate_source_redesign_report.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (out / "candidate_source_redesign_report.html").write_text(html, encoding="utf-8")
        return docs / "latest_candidate_source_redesign_report.html"


def _read(path: str) -> dict:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
