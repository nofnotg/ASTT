from __future__ import annotations

import json

import pandas as pd

from replay_lab.feedback.edge_isolation_report_v54 import EdgeIsolationV54ReportBuilder


def test_edge_isolation_report_v54_outputs(tmp_path):
    store = tmp_path / "replay_store"
    exp = store / "experiments" / "exp_20260101_000000_edge_isolation_v54"
    exp.mkdir(parents=True)
    metrics = {"strategy_results": [], "exit_model_results": [], "module_ablation_results": [], "best_simple_strategy": {}, "trade_review_count": 0, "live_readiness": "LIVE_NOT_ALLOWED"}
    (exp / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    pd.DataFrame({"date_kst": []}).to_parquet(exp / "edge_trades.parquet")
    docs = tmp_path / "docs" / "reports"
    out = EdgeIsolationV54ReportBuilder(store_dir=store, docs_root=docs).build()
    assert out.exists()
    assert (docs / "latest_edge_isolation_v54_summary.json").exists()
    assert (docs / "trade_review_v54.md").exists()
