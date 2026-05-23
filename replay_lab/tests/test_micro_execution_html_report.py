import json

import pandas as pd

from replay_lab.feedback.micro_execution_html_report import MicroExecutionHTMLReportBuilder


def test_micro_execution_html_report_generates_latest_files(tmp_path):
    exp = tmp_path / "experiments" / "exp_20260501_000000_micro_execution"
    exp.mkdir(parents=True)
    (exp / "metrics.json").write_text(json.dumps({"entry_count": 1, "win_rate": 1.0, "profit_factor": 2.0, "expectancy_pct": 0.2, "live_readiness": "LIVE_NOT_ALLOWED"}), encoding="utf-8")
    pd.DataFrame([{"date_kst": "2026-05-01", "market": "KRW-BTC", "entry_decision": "ENTER", "micro_exit_decision": "TAKE_PROFIT", "realized_pnl_pct": 0.2, "data_quality": "PARTIAL"}]).to_parquet(exp / "micro_trades.parquet", index=False)
    docs = tmp_path / "docs"

    path = MicroExecutionHTMLReportBuilder(store_dir=tmp_path, docs_root=docs).build()

    html = path.read_text(encoding="utf-8")
    assert "한눈에 보는 결론" in html
    assert "Profit Factor" in html
    assert (docs / "latest_micro_execution_report.html").exists()
    assert (docs / "latest_micro_execution_summary.json").exists()
