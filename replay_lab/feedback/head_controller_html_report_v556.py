from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR, ROOT_DIR
from replay_lab.research.head_controller_draft_v556 import run_head_controller_draft_v556


class HeadControllerHTMLReportV556:
    def build(self, reports_dir: str | Path = "docs/reports", llm_provider: str = "off", key_file: str | None = None) -> Path:
        result = run_head_controller_draft_v556(reports_dir, llm_provider, key_file)
        summary = {"schema_version": "1.0", "generated_at": datetime.now().isoformat(), **result}
        html = f"""<!doctype html><html><head><meta charset='utf-8'><title>ASTT Head Controller Draft V5.5.6</title><style>body{{font-family:Arial,sans-serif;margin:24px;background:#f6f7f9;color:#17202a}}.card{{background:white;border-radius:8px;padding:16px;margin:12px 0;box-shadow:0 1px 4px #ccd}}</style></head><body><h1>Head Controller Draft V5.5.6</h1><div class='card'><b>live_readiness_opinion:</b> {result['live_readiness_opinion']}<br><b>primary_problem:</b> {result['primary_problem']}<br><b>auto_apply_allowed:</b> {result['auto_apply_allowed']}<br><b>llm_provider:</b> {result.get('llm_config', {}).get('selected_provider', 'off')}</div><div class='card'><h2>Next Experiments</h2><pre>{json.dumps(result['next_experiments'], ensure_ascii=False, indent=2)}</pre></div><div class='card'><h2>Config Proposals</h2><pre>{json.dumps(result['config_proposals'], ensure_ascii=False, indent=2)}</pre></div></body></html>"""
        md = f"# ASTT Head Controller Draft V5.5.6\n\n- live_readiness_opinion: {result['live_readiness_opinion']}\n- primary_problem: {result['primary_problem']}\n- auto_apply_allowed: {result['auto_apply_allowed']}\n- llm_provider: {result.get('llm_config', {}).get('selected_provider', 'off')}\n"
        out = REPLAY_STORE_DIR / "reports" / "head_controller_v556"
        out.mkdir(parents=True, exist_ok=True)
        docs_reports_dir = ROOT_DIR / "docs" / "reports"
        docs_reports_dir.mkdir(parents=True, exist_ok=True)
        (out / "head_controller_report.html").write_text(html, encoding="utf-8")
        (out / "head_controller_report.md").write_text(md, encoding="utf-8")
        (out / "head_controller_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        (docs_reports_dir / "latest_head_controller_draft_report.html").write_text(html, encoding="utf-8")
        (docs_reports_dir / "latest_head_controller_draft_report.md").write_text(md, encoding="utf-8")
        (docs_reports_dir / "latest_head_controller_draft_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return docs_reports_dir / "latest_head_controller_draft_report.html"
