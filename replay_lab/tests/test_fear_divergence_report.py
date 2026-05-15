import json

from replay_lab.feedback.fear_divergence_report import FearDivergenceReportBuilder


def test_fear_divergence_report_writes_outputs(tmp_path):
    reports = tmp_path / "reports" / "fear_divergence_v4"
    reports.mkdir(parents=True)
    exp = tmp_path / "experiments" / "exp_20260101_000000_fear_divergence_v4"
    exp.mkdir(parents=True)
    (exp / "metrics.json").write_text(json.dumps({"entry_count": 0, "live_readiness": "LIVE_NOT_ALLOWED", "skeptic_reject_count": 1}), encoding="utf-8")
    (reports / "fear_divergence_sweep_v4.json").write_text(json.dumps({"best": {"status": "NO_VALID_FEAR_DIVERGENCE_CONFIG"}}), encoding="utf-8")
    (reports / "fear_divergence_compare_v3.json").write_text(json.dumps({"verdict": "V4_INSUFFICIENT_SAMPLE"}), encoding="utf-8")
    builder = FearDivergenceReportBuilder(store_dir=tmp_path, docs_root=tmp_path / "docs" / "reports")
    out = builder.build("2026-01-01", "2026-01-01")
    assert out.exists()
    assert (reports / "fear_divergence_v4_report.json").exists()
    assert (builder.docs_root / "latest_fear_divergence_summary.json").exists()
    assert "V4_INSUFFICIENT_SAMPLE" in out.read_text(encoding="utf-8")
