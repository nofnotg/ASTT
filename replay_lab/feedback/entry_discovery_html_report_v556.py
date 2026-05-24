from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from artifact_integrity.production_report_paths import production_docs_reports_dir, production_replay_report_dir
from artifact_integrity.report_artifact_manifest import build_artifact_manifest
from head_controller.llm_secret_sanitizer import dumps_sanitized
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.research.entry_discovery_v556 import run_entry_discovery_v556
from replay_lab.research.hold_time_sweep_v556 import run_hold_time_sweep_v556
from replay_lab.research.wait_path_analysis_v556 import run_wait_path_analysis_v556


class EntryDiscoveryHTMLReportV556:
    def build(
        self,
        sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555",
        docs_output_dir: str | Path | None = None,
        replay_output_dir: str | Path | None = None,
        generated_by: str = "CLI",
        is_test_artifact: bool = False,
    ) -> Path:
        wait = run_wait_path_analysis_v556(sessions_dir)
        hold = run_hold_time_sweep_v556(sessions_dir)
        discovery = run_entry_discovery_v556(sessions_dir)
        source_session_ids = [path.name for path in Path(sessions_dir).glob("*") if (path / "session_summary.json").exists()]
        source_event_count = sum(1 for path in Path(sessions_dir).glob("*/ledger.jsonl") for _ in path.open(encoding="utf-8"))
        summary = {
            "schema_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "live_readiness": "LIVE_NOT_ALLOWED",
            "candidate_count": wait["candidate_count"],
            "classification_counts": wait["classification_counts"],
            "profiles": discovery["profiles"],
            "artifact_manifest": build_artifact_manifest("ENTRY_DISCOVERY", sessions_dir, wait["candidate_count"], source_session_ids, source_event_count, generated_by, is_test_artifact),
        }
        html = self._html(summary, wait, hold, discovery)
        md = f"# ASTT V5.5.6 Entry Discovery\n\n- live_readiness: LIVE_NOT_ALLOWED\n- candidate_count: {wait['candidate_count']}\n- research_only: true\n"
        out = Path(replay_output_dir) if replay_output_dir else production_replay_report_dir("entry_discovery_v556")
        out.mkdir(parents=True, exist_ok=True)
        docs_reports_dir = Path(docs_output_dir) if docs_output_dir else production_docs_reports_dir()
        docs_reports_dir.mkdir(parents=True, exist_ok=True)
        (out / "entry_discovery_report.html").write_text(html, encoding="utf-8")
        (out / "entry_discovery_report.md").write_text(md, encoding="utf-8")
        (out / "entry_discovery_report.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        (docs_reports_dir / "latest_entry_discovery_report.html").write_text(html, encoding="utf-8")
        (docs_reports_dir / "latest_entry_discovery_report.md").write_text(md, encoding="utf-8")
        (docs_reports_dir / "latest_entry_discovery_summary.json").write_text(dumps_sanitized(summary), encoding="utf-8")
        return docs_reports_dir / "latest_entry_discovery_report.html"

    def _html(self, summary: dict, wait: dict, hold: dict, discovery: dict) -> str:
        return f"""<!doctype html><html><head><meta charset='utf-8'><title>ASTT V5.5.6 Entry Discovery</title><style>body{{font-family:Arial,sans-serif;margin:24px;background:#f6f7f9;color:#17202a}}.card{{background:white;border-radius:8px;padding:16px;margin:12px 0;box-shadow:0 1px 4px #ccd}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px}}</style></head><body><h1>ASTT V5.5.6 Entry Discovery</h1><div class='card'><b>실전 판정:</b> LIVE_NOT_ALLOWED<br><b>중요:</b> WAIT/CANCEL은 매수하지 않은 후보이며 손익에 포함하지 않습니다. 이 보고서는 research-only입니다.</div><div class='card'><h2>WAIT 분류</h2><pre>{json.dumps(wait['classification_counts'], ensure_ascii=False, indent=2)}</pre></div><div class='card'><h2>Hold Sweep</h2><pre>{json.dumps(hold['rows'], ensure_ascii=False, indent=2)}</pre></div><div class='card'><h2>Profiles</h2><pre>{json.dumps(discovery['profiles'], ensure_ascii=False, indent=2)}</pre></div></body></html>"""
