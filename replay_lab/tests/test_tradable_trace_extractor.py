from tradable_winner.tradable_trace_extractor import extract_tradable_traces


def test_tradable_trace_extractor_no_lookahead(tmp_path):
    winner_dir = tmp_path / "tradable_winner"
    winner_dir.mkdir()
    (winner_dir / "tradable_winners.json").write_text('{"winners":[{"winner_id":"w1","market":"KRW-AAA","winner_type":"TRADABLE_SCALP_WINNER","start_time_ms":1000000,"start_price":100,"effective_return_pct":0.5,"estimated_total_cost_pct":0.1,"spread_pct":0.1,"depth_3_level_krw":2000000,"depth_5_level_krw":3000000,"quality":"GOOD"}]}', encoding="utf-8")
    result = extract_tradable_traces(winner_dir, [30, 60], output_dir=tmp_path / "tradable_trace")
    row = result["traces"][0]["trace_windows"]["T_MINUS_30S"]
    assert row["timestamp_ms"] == 970000
