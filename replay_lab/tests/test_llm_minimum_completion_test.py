from llm_ops.llm_token_meter import LLMTokenMeter


def test_llm_minimum_completion_test_meter_counts_completion():
    usage = LLMTokenMeter().from_response_usage(None, "prompt text", '{"summary":"ok"}')
    assert usage.completion_tokens > 0
