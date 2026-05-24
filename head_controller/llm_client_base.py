from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMResult:
    provider: str
    call_success: bool
    content: str
    error: str = ""


class HeadControllerLLMClient:
    provider = "base"

    def analyze(self, context: dict) -> LLMResult:
        raise NotImplementedError
