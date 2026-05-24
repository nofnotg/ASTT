from __future__ import annotations


class LLMRetryPolicy:
    def __init__(self, max_attempts: int = 2):
        self.max_attempts = max(1, max_attempts)

    def should_retry(self, attempt: int, schema_valid: bool, call_success: bool) -> bool:
        return attempt < self.max_attempts and (not schema_valid or not call_success)
