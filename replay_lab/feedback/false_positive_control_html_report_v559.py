from __future__ import annotations

import json
from datetime import datetime

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR


class FalsePositiveControlHTMLReportV559:
    def build(self) -> str:
        fp = json.loads((REPLAY_STORE_DIR / "false_positive" / "false_positive_control.json").read_text(encoding="utf-8"))
        discrim_path = REPLAY_STORE_DIR / "false_positive" / "source_discriminative_power.json"
        refined_path = REPLAY_STORE_DIR / "false_positive" / "refined_source_validation.json"
        summary = {
            "schema_version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            **fp,
            "source_discriminative_power": json.loads(discrim_path.read_text(encoding="utf-8")) if discrim_path.exists() else {},
            "refined_source_validation": json.loads(refined_path.read_text(encoding="utf-8")) if refined_path.exists() else {},
        }
        docs = ROOT_DIR / "docs" / "reports"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "latest_false_positive_control_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        rows = "\n".join(f"| {r['source']} | {r['true_positive_count']} | {r['false_positive_count']} | {r['precision']:.3f} | {r['recall']:.3f} | {r['false_positive_rate']:.3f} |" for r in fp.get("source_results", []))
        md = "# False Positive Control V5.5.9\n\n| Source | TP | FP | Precision | Recall | FPR |\n|---|---:|---:|---:|---:|---:|\n" + rows + "\n"
        html = "<!doctype html><html><head><meta charset='utf-8'><title>False Positive Control V5.5.9</title></head><body><pre>" + json.dumps(summary, ensure_ascii=False, indent=2) + "</pre></body></html>"
        (docs / "latest_false_positive_control_report.md").write_text(md, encoding="utf-8")
        (docs / "latest_false_positive_control_report.html").write_text(html, encoding="utf-8")
        return str(docs / "latest_false_positive_control_report.html")
