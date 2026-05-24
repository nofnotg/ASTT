from execution.timing_based_entry_executor import execute_timing_entry


def test_timing_based_paper_enters_only_from_confirmed_and_never_real_order():
    window = {"effective_return_pct": 0.2, "tradable_with_500k": True, "start_ms": 1, "entry_price": 100}
    assert execute_timing_entry({"state": "CONFIRMED"}, window)["paper_entered"] is True
    assert execute_timing_entry({"state": "WATCH"}, window)["paper_entered"] is False
    assert execute_timing_entry({"state": "CONFIRMED"}, window)["real_order_enabled"] is False
