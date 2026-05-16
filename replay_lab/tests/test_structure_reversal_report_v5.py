import json
from pathlib import Path

from replay_lab.feedback.structure_reversal_report_v5 import StructureReversalV5ReportBuilder


def test_structure_reversal_v5_report_outputs(tmp_path: Path):
    store = tmp_path / "store"
    docs = tmp_path / "docs"
    report_dir = store / "reports" / "structure_reversal_v5"
    report_dir.mkdir(parents=True)
    (report_dir / "structure_reversal_sweep_v5.json").write_text(json.dumps({"best": {"entry_count": 1}}), encoding="utf-8")
    (report_dir / "mtf_context_compare_v5.json").write_text(json.dumps({"best_context_stack": "Daily + 4H", "context_results": []}), encoding="utf-8")
    (report_dir / "structure_reversal_compare_all.json").write_text(json.dumps({"verdict": "V5_INSUFFICIENT_SAMPLE"}), encoding="utf-8")
    html = StructureReversalV5ReportBuilder(store_dir=store, docs_root=docs).build("2026-01-01", "2026-01-05")
    assert html.exists()
    assert (report_dir / "structure_reversal_v5_report.json").exists()
    assert (docs / "latest_structure_reversal_v5_summary.json").exists()
    assert "V3/V4.1/V5" in html.read_text(encoding="utf-8")
