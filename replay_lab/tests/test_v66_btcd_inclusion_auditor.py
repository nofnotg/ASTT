from __future__ import annotations

from analysis.v66_btcd_inclusion_auditor import audit_v66_btcd_inclusion


def test_v66_btcd_inclusion_auditor_reports_terms(tmp_path):
    target = tmp_path / "analysis"
    target.mkdir()
    (target / "v64_policy_compounding_analyzer.py").write_text("btc_dominance_pct = 1", encoding="utf-8")

    result = audit_v66_btcd_inclusion(tmp_path)

    assert result["btcd_in_existing_rolling_edge"] is True
    assert result["evidence"]

