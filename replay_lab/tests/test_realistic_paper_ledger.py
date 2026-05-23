from execution.realistic_paper_ledger import RealisticPaperLedger


def test_realistic_paper_ledger_appends_events_and_positions(tmp_path):
    ledger = RealisticPaperLedger(tmp_path)
    ledger.append("CANDIDATE", {"entry_decision": "WAIT"})
    ledger.append("POSITION_OPENED", {"position_id": "p1"})
    ledger.append("POSITION_CLOSED", {"position_id": "p1", "pnl_krw": 10})
    assert (tmp_path / "ledger.jsonl").exists()
    assert (tmp_path / "positions.jsonl").exists()
    assert (tmp_path / "trades.jsonl").exists()
