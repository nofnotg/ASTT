from llm_ops.llm_budget_policy import LLMBudgetPolicy


def test_llm_budget_policy_compresses_or_skips_over_budget():
    assert LLMBudgetPolicy(max_prompt_tokens=10).evaluate(11)["action"] == "COMPRESS_OR_SKIP"
