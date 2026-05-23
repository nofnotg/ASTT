from execution.forward_paper_micro_runner import run_forward_paper_micro_session
from replay_lab.replay.forward_micro_replay import replay_recorded_micro_session


def test_forward_micro_replay_replays_session(tmp_path, monkeypatch):
    monkeypatch.setattr("execution.forward_paper_micro_runner.REPLAY_STORE_DIR", tmp_path)
    result = run_forward_paper_micro_session(duration_minutes=1, markets=["KRW-BTC"], top_markets=1)

    replay = replay_recorded_micro_session(result["session_id"], root=tmp_path, output_dir=tmp_path / "replayed")

    assert replay["trade_event_count"] > 0
    assert replay["event_count"] > 0
