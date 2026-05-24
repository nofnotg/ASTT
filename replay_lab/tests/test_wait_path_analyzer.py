import json

from execution.wait_path_analyzer import analyze_wait_paths


def test_wait_path_analyzer_reads_ledger(tmp_path):
    session = tmp_path / "s1"
    session.mkdir()
    events = [
        {"event_type": "SNAPSHOT", "market": "KRW-BTC", "timestamp_ms": 1000, "last_price": 100},
        {"event_type": "CANDIDATE", "candidate_id": "c1", "market": "KRW-BTC", "candidate_source": "MICRO_ACCELERATION", "candidate_time_ms": 1000, "reference_price": 100},
        {"event_type": "SNAPSHOT", "market": "KRW-BTC", "timestamp_ms": 2000, "last_price": 99.5},
    ]
    (session / "ledger.jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    result = analyze_wait_paths(tmp_path)
    assert result["candidate_count"] == 1
    assert result["included_in_pnl"] is False
