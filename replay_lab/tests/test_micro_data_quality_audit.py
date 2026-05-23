from execution.forward_paper_micro_runner import run_forward_paper_micro_session
from replay_lab.research.micro_data_quality_audit import audit_micro_data_quality


def test_micro_data_quality_audit_counts_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr("execution.forward_paper_micro_runner.REPLAY_STORE_DIR", tmp_path)
    run_forward_paper_micro_session(duration_minutes=1, markets=["KRW-BTC"], top_markets=1)

    result = audit_micro_data_quality(tmp_path / "sessions" / "live_micro")

    assert result["session_count"] == 1
    assert result["replayable_session_count"] == 1
