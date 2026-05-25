from __future__ import annotations

from btcd.global_btcd_loader import load_global_btcd


def test_global_btcd_loader_reports_unavailable_without_fake_data(tmp_path):
    frame, quality = load_global_btcd(tmp_path / "missing.csv")

    assert frame.empty
    assert quality["available"] is False
    assert "Fake dominance was not generated" in quality["notes"]

