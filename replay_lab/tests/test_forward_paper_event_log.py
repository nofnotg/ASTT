from execution.forward_paper_event_log import ForwardPaperEventLog


def test_forward_paper_event_log_appends_in_order(tmp_path):
    log = ForwardPaperEventLog("session_test", root=tmp_path)
    log.append("SETUP_FOUND", "KRW-BTC", "IDLE", "SETUP_FOUND")
    log.append("ENTER", "KRW-BTC", "ARMED", "ENTERED")

    assert [row["event_type"] for row in log.read()] == ["SETUP_FOUND", "ENTER"]
