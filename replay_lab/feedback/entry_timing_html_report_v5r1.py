from __future__ import annotations

import json
from pathlib import Path


class EntryTimingHTMLReportV5R1:
    def build(self, output_dir: str | Path = "docs/reports") -> dict:
        labels = _read(Path("replay_store/timing_labels/latest_timing_labels.json"))
        windows = _read(Path("replay_store/timing_state_replay/latest_entry_window_summary.json"))
        states = _read(Path("replay_store/timing_state_replay/latest_state_machine_summary.json"))
        paper = _read(Path("replay_store/timing_state_replay/latest_timing_based_paper_summary.json"))
        summary = {**windows, "label_counts": labels.get("label_counts", {}), "state_transition_counts": states.get("transition_counts", {}), "abort_reason_counts": states.get("abort_reason_counts", {}), "paper_execution": paper, "real_order_enabled": False}
        return _write(output_dir, "latest_entry_timing", "ASTT V5.R1 Entry Timing Report", summary)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write(output_dir: str | Path, stem: str, title: str, summary: dict) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{stem}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    sections = [
        "ENTRY_WINDOW Count",
        "TOO_EARLY / TOO_LATE / FAKE_SIGNAL Distribution",
        "LIQUIDITY_TRAP / SPREAD_TRAP Distribution",
        "State Transition Table",
        "WATCH -> ARMED -> TRIGGERED -> CONFIRMED Rate",
        "Paper ENTER Status",
        "500k KRW Effective Return",
        "Timing Failure Reasons",
        "Next Improvement Points",
    ]
    md = "# " + title + "\n\n" + "\n".join(f"## {s}\n\n```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```\n" for s in sections)
    (out / f"{stem}_report.md").write_text(md, encoding="utf-8")
    html = "".join(f"<h2>{s}</h2><pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre>" for s in sections)
    (out / f"{stem}_report.html").write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head><body><h1>{title}</h1>{html}</body></html>", encoding="utf-8")
    return summary
