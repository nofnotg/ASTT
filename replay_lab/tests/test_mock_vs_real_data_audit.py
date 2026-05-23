import json

from replay_lab.research.mock_vs_real_data_audit import audit_mock_vs_real_data


def test_mock_vs_real_data_audit_separates_sources(tmp_path):
    mock = tmp_path / "live_micro" / "m1"
    real = tmp_path / "upbit_ws" / "r1"
    mock.mkdir(parents=True)
    real.mkdir(parents=True)
    (mock / "session_summary.json").write_text(json.dumps({"data_source": "MOCK", "eligible_for_live_readiness": False}), encoding="utf-8")
    (real / "session_summary.json").write_text(json.dumps({"data_source": "UPBIT_WS", "eligible_for_live_readiness": True}), encoding="utf-8")

    result = audit_mock_vs_real_data(tmp_path)

    assert result["mock_session_count"] == 1
    assert result["real_session_count"] == 1
    assert result["readiness_eligible_session_count"] == 1
