from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from artifact_integrity.production_report_paths import production_docs_reports_dir, production_replay_report_dir
from features.winner_trace_features import summarize_winner_trace_features
from head_controller.llm_secret_sanitizer import dumps_sanitized


class WinnerTraceHTMLReportV558:
    def build(self) -> Path:
        data = _read("replay_store/winner_mining/events/winner_events.json")
        traces = _read("replay_store/winner_mining/traces/winner_traces.json")
        trace_rows = traces.get("traces", [])
        summary = {
            "schema_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            **data.get("summary", {}),
            "feature_summary": summarize_winner_trace_features(trace_rows),
            "trace_summary": traces.get("summary", {}),
            "live_readiness": "LIVE_NOT_ALLOWED",
        }
        html = _html("Winner Trace Mining V5.5.8", summary)
        md = f"# Winner Trace Mining V5.5.8\n\n- winner_event_count: {summary.get('winner_event_count', 0)}\n- live_readiness: LIVE_NOT_ALLOWED\n"
        docs = production_docs_reports_dir()
        out = production_replay_report_dir("winner_trace_v558")
        (docs / "latest_winner_trace_summary.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (docs / "latest_winner_trace_report.html").write_text(html, encoding="utf-8")
        (docs / "latest_winner_trace_report.md").write_text(md, encoding="utf-8")
        (out / "winner_trace_report.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (out / "winner_trace_report.html").write_text(html, encoding="utf-8")
        return docs / "latest_winner_trace_report.html"


def _read(path: str) -> dict:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _html(title: str, summary: dict) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head><body><h1>{title}</h1><p>실제 주문 금지. winner mining은 research mode입니다.</p><pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre></body></html>"
