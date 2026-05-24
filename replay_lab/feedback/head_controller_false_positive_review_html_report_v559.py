from __future__ import annotations

import json
from datetime import datetime

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR


class HeadControllerFalsePositiveReviewHTMLReportV559:
    def build(self) -> str:
        payload = json.loads((REPLAY_STORE_DIR / "false_positive" / "head_controller_false_positive_review.json").read_text(encoding="utf-8"))
        summary = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), **payload}
        docs = ROOT_DIR / "docs" / "reports"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "latest_head_controller_false_positive_review_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        md = f"""# Head Controller False Positive Review V5.5.9

- primary_problem: {summary.get('primary_problem')}
- auto_apply_allowed: {summary.get('auto_apply_allowed')}
- live_order_allowed: {summary.get('live_order_allowed')}
"""
        html = "<!doctype html><html><head><meta charset='utf-8'><title>Head Controller False Positive Review V5.5.9</title></head><body><pre>" + json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "</pre></body></html>"
        (docs / "latest_head_controller_false_positive_review_report.md").write_text(md, encoding="utf-8")
        (docs / "latest_head_controller_false_positive_review_report.html").write_text(html, encoding="utf-8")
        return str(docs / "latest_head_controller_false_positive_review_report.html")
