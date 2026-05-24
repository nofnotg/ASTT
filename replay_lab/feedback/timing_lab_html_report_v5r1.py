from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


class TimingLabHTMLReportV5R1:
    def build(self, output_dir: str | Path = "docs/reports") -> dict:
        summary = _read(REPLAY_STORE_DIR / "timing_lab" / "latest_timing_lab_summary.json")
        sections = [
            "Executive Summary",
            "Winner Mining Limitations",
            "Event-Driven Timing Lab Structure",
            "Event Type Counts",
            "Clip Collection Result",
            "Clip Quality",
            "Event Time Distribution",
            "Market State Summary",
            "Next Collection Plan",
        ]
        return _write_report(output_dir, "latest_timing_lab", "ASTT V5.R1 Timing Lab Report", summary, sections)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write_report(output_dir: str | Path, stem: str, title: str, summary: dict, sections: list[str]) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    safe = {"schema_version": "v5r1", "real_order_enabled": False, **summary}
    (out / f"{stem}_summary.json").write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")
    md = "# " + title + "\n\n" + "\n".join(f"## {section}\n\n```json\n{json.dumps(safe, ensure_ascii=False, indent=2)}\n```\n" for section in sections)
    (out / f"{stem}_report.md").write_text(md, encoding="utf-8")
    html_sections = "".join(f"<h2>{section}</h2><pre>{json.dumps(safe, ensure_ascii=False, indent=2)}</pre>" for section in sections)
    (out / f"{stem}_report.html").write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head><body><h1>{title}</h1>{html_sections}</body></html>", encoding="utf-8")
    return safe
