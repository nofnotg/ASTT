from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from artifact_integrity.production_report_paths import production_docs_reports_dir, production_replay_report_dir
from head_controller.llm_secret_sanitizer import dumps_sanitized
from replay_lab.research.artifact_integrity_check_v5561 import scan_report_secrets_v5561
from replay_lab.research.head_controller_openai_live_check_v5562 import (
    run_head_controller_openai_live_smoke_v5562,
    run_head_controller_unsafe_prompt_test_v5562,
)


class HeadControllerOpenAILiveReportV5562:
    def build(self, reports_dir: str | Path = "docs/reports", llm_provider: str = "openai", key_file: str | None = None) -> Path:
        smoke = run_head_controller_openai_live_smoke_v5562(reports_dir, llm_provider, key_file)
        unsafe = run_head_controller_unsafe_prompt_test_v5562(llm_provider)
        secret = scan_report_secrets_v5561(reports_dir)
        summary = {
            "schema_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "live_readiness": "LIVE_NOT_ALLOWED",
            "openai_live_smoke": smoke,
            "unsafe_prompt_test": unsafe,
            "secret_scan": secret,
            "auto_apply_allowed": False,
            "live_order_allowed": False,
        }
        html = _html(summary)
        md = _md(summary)
        docs = production_docs_reports_dir()
        out = production_replay_report_dir("head_controller_openai_live_v5562")
        (docs / "latest_head_controller_openai_live_summary.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (docs / "latest_head_controller_openai_live_report.html").write_text(html, encoding="utf-8")
        (docs / "latest_head_controller_openai_live_report.md").write_text(md, encoding="utf-8")
        (out / "head_controller_openai_live_report.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (out / "head_controller_openai_live_report.html").write_text(html, encoding="utf-8")
        return docs / "latest_head_controller_openai_live_report.html"


def _html(summary: dict) -> str:
    smoke = summary["openai_live_smoke"]
    unsafe = summary["unsafe_prompt_test"]
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>OpenAI Live Guard V5.5.6.2</title>"
        "<style>body{font-family:Arial,sans-serif;margin:24px;background:#f6f7f9;color:#111}.card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:16px;margin:12px 0}</style></head><body>"
        "<h1>Head Controller OpenAI Live Guard V5.5.6.2</h1>"
        "<div class='card'><b>실제 주문 금지.</b> LLM은 연구 보조자이며 active config 자동 적용은 금지됩니다.</div>"
        f"<div class='card'><h2>Smoke</h2><p>provider: {smoke.get('provider')} / call_success: {smoke.get('call_success')} / schema_valid: {smoke.get('schema_valid')} / fallback_used: {smoke.get('fallback_used')}</p></div>"
        f"<div class='card'><h2>Unsafe Prompt</h2><p>unsafe_detected: {unsafe.get('unsafe_proposal_detected')} / auto_apply_allowed: false / live_order_allowed: false</p></div>"
        f"<div class='card'><h2>Secret Scan</h2><p>{summary['secret_scan'].get('secret_scan_status')}</p></div>"
        "</body></html>"
    )


def _md(summary: dict) -> str:
    smoke = summary["openai_live_smoke"]
    unsafe = summary["unsafe_prompt_test"]
    return (
        "# Head Controller OpenAI Live Guard V5.5.6.2\n\n"
        f"- provider: {smoke.get('provider')}\n"
        f"- call_success: {smoke.get('call_success')}\n"
        f"- schema_valid: {smoke.get('schema_valid')}\n"
        f"- fallback_used: {smoke.get('fallback_used')}\n"
        f"- unsafe_proposal_detected: {unsafe.get('unsafe_proposal_detected')}\n"
        "- auto_apply_allowed: false\n"
        "- live_order_allowed: false\n"
    )
