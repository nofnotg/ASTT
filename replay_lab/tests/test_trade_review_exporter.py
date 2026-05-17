from __future__ import annotations

import pandas as pd

from features.trade_review_exporter import build_trade_review_rows, export_trade_review


def test_trade_review_exporter_md_csv(tmp_path):
    rows = build_trade_review_rows(pd.DataFrame([{"date_kst": "2026-01-01", "market": "KRW-BTC", "strategy_id": "MTF_ONLY", "realized_pnl_pct": 1.0, "mfe_pct": 1.5, "mae_pct": -0.4}]))
    md = tmp_path / "review.md"
    csv = tmp_path / "review.csv"
    export_trade_review(rows, md, csv)
    assert "Trade Review" in md.read_text(encoding="utf-8")
    assert "review_question" in csv.read_text(encoding="utf-8")
    assert rows[0]["actual_path_summary"]
