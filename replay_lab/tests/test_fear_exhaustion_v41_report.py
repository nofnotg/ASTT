import json
from pathlib import Path

from replay_lab.feedback.fear_exhaustion_v41_report import FearExhaustionV41ReportBuilder


def test_v41_report_writes_html_json_md_and_docs(tmp_path: Path):
    store = tmp_path / "replay_store"
    docs = tmp_path / "docs" / "reports"
    report_dir = store / "reports" / "fear_exhaustion_v41"
    report_dir.mkdir(parents=True)
    (report_dir / "fear_exhaustion_sweep_v41.json").write_text(
        json.dumps(
            {
                "best": {"timeframe": "1m", "entry_count": 30, "profit_factor": 1.0, "account_return_pct": 0.1},
                "base_funnels": {"1m": {"timeframe": "1m", "total_bars": 100, "drop_event_count": 20, "final_entry_count": 5}},
                "results": [{"timeframe": "1m", "entry_count": 30, "profit_factor": 1.0, "account_return_pct": 0.1, "win_rate": 0.5}],
            }
        ),
        encoding="utf-8",
    )
    builder = FearExhaustionV41ReportBuilder(store_dir=store, docs_root=docs)
    html = builder.build("2026-01-01", "2026-01-05")
    assert html.exists()
    assert (report_dir / "fear_exhaustion_v41_report.json").exists()
    assert (report_dir / "fear_exhaustion_v41_report.md").exists()
    assert (docs / "latest_fear_exhaustion_v41_summary.json").exists()
    assert "1m vs 5m" in html.read_text(encoding="utf-8")
