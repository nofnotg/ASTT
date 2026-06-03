from __future__ import annotations

from llm_council.llm_input_pack_builder import build_input_pack


def test_v688_llm_input_pack_does_not_include_raw_logs(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    pack = build_input_pack("daily", reports)
    assert pack["raw_log_included"] is False
    assert pack["token_budget"]["raw_log_allowed"] is False
    assert "OPENAI_API_KEY" not in str(pack)
