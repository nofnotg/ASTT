from execution.forward_paper_micro_runner import run_forward_paper_micro_session
from replay_lab.research.micro_cost_survival_test import run_micro_cost_survival_test


def test_micro_cost_survival_test_returns_live_readiness(tmp_path, monkeypatch):
    monkeypatch.setattr("execution.forward_paper_micro_runner.REPLAY_STORE_DIR", tmp_path)
    run_forward_paper_micro_session(duration_minutes=1, markets=["KRW-BTC"], top_markets=1)

    result = run_micro_cost_survival_test(tmp_path / "sessions" / "live_micro")

    assert "realistic_1_survives" in result
    assert result["live_readiness"] in {"LIVE_NOT_ALLOWED", "PAPER_MORE_REQUIRED"}
