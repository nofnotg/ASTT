import json

from replay_lab.feedback.entry_discovery_html_report_v556 import EntryDiscoveryHTMLReportV556


def test_entry_discovery_report_generates(tmp_path, monkeypatch):
    session = tmp_path / "s1"
    session.mkdir()
    events = [
        {"event_type": "SNAPSHOT", "market": "KRW-BTC", "timestamp_ms": 1000, "last_price": 100},
        {"event_type": "CANDIDATE", "candidate_id": "c1", "market": "KRW-BTC", "candidate_source": "VWAP_RECLAIM", "candidate_time_ms": 1000, "reference_price": 100},
    ]
    (session / "ledger.jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    out = EntryDiscoveryHTMLReportV556().build(tmp_path)
    assert out.exists()
