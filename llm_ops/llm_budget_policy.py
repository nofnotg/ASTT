from __future__ import annotations


class LLMBudgetPolicy:
    def __init__(self, max_prompt_tokens: int = 8000, max_total_tokens: int = 12000):
        self.max_prompt_tokens = max_prompt_tokens
        self.max_total_tokens = max_total_tokens

    def evaluate(self, prompt_tokens: int, total_tokens: int = 0) -> dict:
        over = prompt_tokens > self.max_prompt_tokens or total_tokens > self.max_total_tokens
        return {"allowed": not over, "action": "COMPRESS_OR_SKIP" if over else "ALLOW", "budget_exceeded": over}
