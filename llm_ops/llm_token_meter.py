from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMTokenMeter:
    def count_text(self, text: str) -> int:
        return max(1, len(text) // 4) if text else 0

    def from_response_usage(self, usage: dict | None, prompt: str = "", completion: str = "") -> TokenUsage:
        usage = usage or {}
        prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or self.count_text(prompt))
        completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or self.count_text(completion))
        total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
        return TokenUsage(prompt_tokens, completion_tokens, total_tokens)

    def estimate_cost_usd(self, usage: TokenUsage, prompt_per_1m: float = 5.0, completion_per_1m: float = 15.0) -> float:
        return (usage.prompt_tokens / 1_000_000 * prompt_per_1m) + (usage.completion_tokens / 1_000_000 * completion_per_1m)
