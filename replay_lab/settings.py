from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ReplaySettings:
    candle_rps_limit: int = int(os.getenv("REPLAY_UPBIT_CANDLE_RPS_LIMIT", "8"))
    backoff_seconds: float = float(os.getenv("REPLAY_BACKOFF_SECONDS", "1.0"))
    max_retry: int = int(os.getenv("REPLAY_MAX_RETRY", "3"))
    enable_athena_llm: bool = os.getenv("ENABLE_ATHENA_LLM", "false").lower() == "true"
    athena_min_sample_size: int = int(os.getenv("ATHENA_MIN_SAMPLE_SIZE", "100"))

