from __future__ import annotations

import json
from datetime import datetime

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR


class RedesignedSourceForwardHTMLReportV559:
    def build(self) -> str:
        payload = json.loads((REPLAY_STORE_DIR / "forward_v559" / "latest_forward_summary.json").read_text(encoding="utf-8"))
        full_seed_path = REPLAY_STORE_DIR / "false_positive" / "full_seed_refined_source_validation.json"
        summary = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), **payload}
        if full_seed_path.exists():
            summary["full_seed_refined_source_validation"] = json.loads(full_seed_path.read_text(encoding="utf-8"))
        docs = ROOT_DIR / "docs" / "reports"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "latest_redesigned_source_forward_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        md = f"""# Redesigned Source Forward V5.5.9

- session_id: {summary.get('session_id')}
- candidate_count: {summary.get('candidate_count')}
- ENTER: {summary.get('ENTER')}
- paper_trade_count: {summary.get('paper_trade_count')}
- pnl_evaluable: {summary.get('pnl_evaluable')}
"""
        html = "<!doctype html><html><head><meta charset='utf-8'><title>Redesigned Source Forward V5.5.9</title></head><body><pre>" + json.dumps(summary, ensure_ascii=False, indent=2) + "</pre></body></html>"
        (docs / "latest_redesigned_source_forward_report.md").write_text(md, encoding="utf-8")
        (docs / "latest_redesigned_source_forward_report.html").write_text(html, encoding="utf-8")
        return str(docs / "latest_redesigned_source_forward_report.html")
