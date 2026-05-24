from __future__ import annotations

import json
from pathlib import Path


class HeadControllerTimingReviewHTMLReportV5R1:
    def build(self, output_dir: str | Path = "docs/reports") -> dict:
        summary = _read(Path("replay_store/timing_lab/head_controller_timing_review.json"))
        return _write(output_dir, "latest_head_controller_timing_review", "ASTT V5.R1 Head Controller Timing Review", summary)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"live_readiness_opinion": "LIVE_NOT_ALLOWED", "auto_apply_allowed": False, "live_order_allowed": False}


def _write(output_dir: str | Path, stem: str, title: str, summary: dict) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    safe = {**summary, "auto_apply_allowed": False, "live_order_allowed": False}
    (out / f"{stem}_summary.json").write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")
    sections = [
        "Head Controller Summary",
        "Primary Problem",
        "Timing Assessment",
        "Recommended Event Types",
        "Event Types To Pause",
        "State Transition Findings",
        "Next Experiments",
        "Risk Flags",
        "Config Proposals",
        "Auto Apply Disabled",
        "Live Order Disabled",
    ]
    md = "# " + title + "\n\n" + "\n".join(f"## {s}\n\n```json\n{json.dumps(safe, ensure_ascii=False, indent=2)}\n```\n" for s in sections)
    (out / f"{stem}_report.md").write_text(md, encoding="utf-8")
    html = "".join(f"<h2>{s}</h2><pre>{json.dumps(safe, ensure_ascii=False, indent=2)}</pre>" for s in sections)
    (out / f"{stem}_report.html").write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head><body><h1>{title}</h1>{html}</body></html>", encoding="utf-8")
    return safe
