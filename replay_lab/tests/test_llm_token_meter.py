from llm_ops.llm_token_meter import LLMTokenMeter


def test_llm_token_meter_records_tokens_and_cost():
    meter = LLMTokenMeter()
    usage = meter.from_response_usage({"prompt_tokens": 10, "completion_tokens": 5})
    assert usage.total_tokens == 15
    assert meter.estimate_cost_usd(usage) > 0
