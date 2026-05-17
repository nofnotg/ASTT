from pathlib import Path
from replay_lab.feedback.fractal_v52_report import FractalV52ReportBuilder


def test_fractal_v52_report_outputs(tmp_path: Path):
    store = tmp_path / "store"
    docs = tmp_path / "docs"
    out = FractalV52ReportBuilder(store_dir=store, docs_root=docs).build("2026-01-01", "2026-01-05")
    assert out.exists()
    assert (store / "reports" / "fractal_v52" / "fractal_v52_report.json").exists()
    assert (docs / "latest_fractal_v52_summary.json").exists()
