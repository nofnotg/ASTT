from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from artifact_integrity.production_report_paths import production_docs_reports_dir, production_replay_report_dir
from head_controller.llm_secret_sanitizer import dumps_sanitized
from replay_lab.research.ladder_entry_exit_validation_v557 import validate_ladder_entry_exit_v557
from replay_lab.research.sizing_mode_comparison_v557 import compare_sizing_modes_v557


class FullSeedAllocatorHTMLReportV557:
    def build(self) -> Path:
        sizing = compare_sizing_modes_v557()
        ladder = validate_ladder_entry_exit_v557()
        summary = _read_session_summary()
        summary = {"schema_version": "1.0", "generated_at": datetime.now().isoformat(), **summary, "sizing_mode_comparison": sizing, "ladder_validation": ladder}
        html = _html(summary)
        md = _md(summary)
        docs = production_docs_reports_dir()
        out = production_replay_report_dir("full_seed_allocator_v557")
        (docs / "latest_full_seed_allocator_summary.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (docs / "latest_full_seed_allocator_report.html").write_text(html, encoding="utf-8")
        (docs / "latest_full_seed_allocator_report.md").write_text(md, encoding="utf-8")
        (out / "full_seed_allocator_report.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (out / "full_seed_allocator_report.html").write_text(html, encoding="utf-8")
        return docs / "latest_full_seed_allocator_report.html"


def _read_session_summary() -> dict:
    path = Path("replay_store/reports/full_seed_allocator_v557/full_seed_session.json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _html(summary: dict) -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>Full Seed Allocator V5.5.7</title>"
        "<style>body{font-family:Arial,sans-serif;margin:24px;background:#f7f8fa}.card{background:white;border:1px solid #ddd;border-radius:8px;padding:16px;margin:12px 0}</style></head><body>"
        "<h1>50만 원 Full Seed Allocator Research Mode</h1>"
        "<div class='card'>실제 주문은 금지되어 있으며, ENTER 0이면 수익률은 평가하지 않습니다.</div>"
        f"<div class='card'>candidate: {summary.get('candidate_count')} / ENTER: {summary.get('enter_count')} / trade: {summary.get('trade_count')} / primary: {summary.get('primary_problem')}</div>"
        "</body></html>"
    )


def _md(summary: dict) -> str:
    return f"# Full Seed Allocator V5.5.7\n\n- candidate: {summary.get('candidate_count')}\n- ENTER: {summary.get('enter_count')}\n- trade: {summary.get('trade_count')}\n- primary_problem: {summary.get('primary_problem')}\n"
