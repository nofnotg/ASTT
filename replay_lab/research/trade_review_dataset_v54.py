from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from features.trade_review_exporter import build_trade_review_rows, export_trade_review
from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR
from replay_lab.replay.edge_isolation_v54 import latest_edge_isolation_v54_experiment


def export_trade_review_v54(start_date: date, end_date: date, top_markets: int = 50, store_dir: Path = REPLAY_STORE_DIR, docs_root: Path = ROOT_DIR / "docs" / "reports") -> Path:
    out_dir = store_dir / "reports" / "edge_isolation_v54"
    out_dir.mkdir(parents=True, exist_ok=True)
    exp = latest_edge_isolation_v54_experiment(store_dir)
    trades = pd.read_parquet(exp / "edge_trades.parquet") if exp and (exp / "edge_trades.parquet").exists() else pd.DataFrame()
    if not trades.empty:
        trades = trades.sort_values(["date_kst", "strategy_id", "exit_model"]).groupby(["date_kst", "market"], as_index=False).head(1)
    rows = build_trade_review_rows(trades)
    export_trade_review(rows, docs_root / "trade_review_v54.md", docs_root / "trade_review_v54.csv")
    export_trade_review(rows, out_dir / "trade_review_v54.md", out_dir / "trade_review_v54.csv")
    html_rows = "".join(f"<tr><td>{r['date']}</td><td>{r['market']}</td><td>{r['strategy_id']}</td><td>{r['realized_pnl_pct']}</td><td>{r['review_question']}</td></tr>" for r in rows)
    (out_dir / "trade_review_v54.html").write_text(f"<html><body><h1>Trade Review V5.4</h1><table>{html_rows}</table></body></html>", encoding="utf-8")
    return out_dir
