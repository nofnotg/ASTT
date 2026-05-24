from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from artifact_integrity.production_report_paths import production_docs_reports_dir, production_replay_report_dir
from head_controller.llm_secret_sanitizer import dumps_sanitized
from replay_lab.research.artifact_integrity_check_v5561 import scan_report_secrets_v5561
from replay_lab.research.head_controller_llm_guard_v5561 import run_head_controller_llm_guard_v5561


class HeadControllerLLMGuardReportV5561:
    def build(self, reports_dir: str | Path = "docs/reports", llm_provider: str = "auto", key_file: str | None = None) -> Path:
        result = run_head_controller_llm_guard_v5561(reports_dir, llm_provider, key_file, smoke=False)
        secret = scan_report_secrets_v5561(reports_dir)
        summary = {"schema_version": "1.0", "generated_at": datetime.now().isoformat(), **result, "secret_scan": secret}
        html = f"<!doctype html><html><body><h1>Head Controller LLM Guard V5.5.6.1</h1><p>실제 주문 금지. active config 자동 적용 금지. LLM은 연구 보조자입니다.</p><pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre></body></html>"
        md = f"# Head Controller LLM Guard V5.5.6.1\n\n- provider: {result.get('provider')}\n- call_success: {result.get('call_success')}\n- fallback_used: {result.get('fallback_used')}\n- auto_apply_allowed: false\n- live_order_allowed: false\n"
        docs = production_docs_reports_dir()
        out = production_replay_report_dir("head_controller_llm_guard_v5561")
        (docs / "latest_head_controller_llm_guard_report.html").write_text(html, encoding="utf-8")
        (docs / "latest_head_controller_llm_guard_report.md").write_text(md, encoding="utf-8")
        (docs / "latest_head_controller_llm_guard_summary.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (out / "head_controller_llm_guard_report.html").write_text(html, encoding="utf-8")
        (out / "head_controller_llm_guard_report.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        return docs / "latest_head_controller_llm_guard_report.html"
