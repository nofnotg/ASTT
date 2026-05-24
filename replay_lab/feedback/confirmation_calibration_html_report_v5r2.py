from __future__ import annotations

import json
from pathlib import Path


class ConfirmationCalibrationHTMLReportV5R2:
    def build(self, output_dir: str | Path = "docs/reports") -> dict:
        summary = {"armed": _read("replay_store/calibration/armed_calibration.json"), "confirmation": _read("replay_store/calibration/confirmation_calibration.json"), "grid": _read("replay_store/calibration/calibration_grid.json")}
        return _write(output_dir, "latest_confirmation_calibration", "ASTT V5.R2 Confirmation Calibration", summary)


def _read(path: str | Path) -> dict:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(output_dir: str | Path, stem: str, title: str, summary: dict) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{stem}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    sections = [
        "WATCH -> ARMED Problem",
        "TRIGGERED -> CONFIRMED Problem",
        "ARMED Calibration Result",
        "CONFIRMED Calibration Result",
        "Top 3 Calibration Config",
        "Fake After Confirm Risk",
        "Paper ENTER Possibility",
        "Recommended Config Without Active Apply",
    ]
    md = "# " + title + "\n\n" + "\n".join(f"## {s}\n\n```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```\n" for s in sections)
    (out / f"{stem}_report.md").write_text(md, encoding="utf-8")
    html = "".join(f"<h2>{s}</h2><pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre>" for s in sections)
    (out / f"{stem}_report.html").write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head><body><h1>{title}</h1>{html}</body></html>", encoding="utf-8")
    return summary
