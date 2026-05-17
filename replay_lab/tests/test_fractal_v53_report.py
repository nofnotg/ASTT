from __future__ import annotations

import json

from replay_lab.feedback.fractal_v53_report import FractalV53ReportBuilder


def test_fractal_v53_report_generates_files(tmp_path):
    store = tmp_path / "replay_store"
    exp = store / "experiments" / "exp_20260101_000000_fractal_v53"
    exp.mkdir(parents=True)
    (exp / "metrics.json").write_text(json.dumps({"entry_count": 0, "initial_equity_krw": 500000, "final_equity_krw": 500000, "full_validation_completed": False}), encoding="utf-8")
    import pandas as pd

    pd.DataFrame({"date_kst": []}).to_parquet(exp / "paper_trades.parquet")
    docs = tmp_path / "docs" / "reports"
    out = FractalV53ReportBuilder(store_dir=store, docs_root=docs).build()
    assert out.exists()
    assert (store / "reports" / "fractal_v53" / "fractal_v53_report.json").exists()
    assert (docs / "latest_fractal_v53_summary.json").exists()
