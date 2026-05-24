import json

from head_controller.head_controller_context_builder import build_head_controller_context


def test_head_controller_context_reads_reports(tmp_path):
    (tmp_path / "latest_realistic_paper_summary.json").write_text(json.dumps({"trade_count": 0}), encoding="utf-8")
    ctx = build_head_controller_context(tmp_path)
    assert ctx["session_summary"]["trade_count"] == 0
    assert ctx["constraints"]["auto_apply_config"] is False
