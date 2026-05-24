from replay_lab.feedback.tradable_winner_mining_html_report_v5510 import TradableWinnerMiningHTMLReportV5510


def test_tradable_winner_mining_report_builds(tmp_path):
    result = TradableWinnerMiningHTMLReportV5510().build(tmp_path)
    assert (tmp_path / "latest_tradable_winner_mining_report.html").exists()
    assert result["schema_version"] == "1.0"
