from llm_ops.llm_usage_logger import LLMUsageLogger


def test_llm_usage_logger_writes_jsonl_and_aggregates_by_purpose(tmp_path):
    logger = LLMUsageLogger(tmp_path)
    logger.log({"purpose": "HEAD_CONTROLLER_TIMING_REVIEW", "total_tokens": 10})
    summary = logger.aggregate()
    assert summary["total_call_count"] == 1
    assert summary["tokens_by_purpose"]["HEAD_CONTROLLER_TIMING_REVIEW"] == 10
