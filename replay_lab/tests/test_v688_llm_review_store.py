from __future__ import annotations

from llm_council.llm_fallback_writer import build_llm_review


def test_v688_llm_review_fallback_is_safe(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    payload = build_llm_review("daily", reports)
    assert payload["fallback_used"] is True
    assert payload["llm_used"] is False
    assert payload["active_change_applied"] is False
    assert payload["api_key_value_stored"] is False
