from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


class LLMUsageLogger:
    def __init__(self, root: str | Path = "replay_store/llm_usage"):
        self.root = Path(root)
        self.path = self.root / "llm_usage.jsonl"

    def log(self, row: dict[str, Any]) -> dict[str, Any]:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {
            "llm_call_id": row.get("llm_call_id") or f"llm_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            "timestamp": row.get("timestamp") or datetime.utcnow().isoformat(),
            "provider": row.get("provider", "off"),
            "model": row.get("model", "none"),
            "purpose": row.get("purpose", "UNKNOWN"),
            "prompt_tokens": int(row.get("prompt_tokens", 0)),
            "completion_tokens": int(row.get("completion_tokens", 0)),
            "total_tokens": int(row.get("total_tokens", 0)),
            "estimated_cost_usd": float(row.get("estimated_cost_usd", 0.0)),
            "input_report_count": int(row.get("input_report_count", 0)),
            "fallback_used": bool(row.get("fallback_used", False)),
            "schema_valid": bool(row.get("schema_valid", True)),
            "unsafe_proposal_detected": bool(row.get("unsafe_proposal_detected", False)),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return payload

    def aggregate(self) -> dict[str, Any]:
        rows = []
        if self.path.exists():
            rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        by_purpose = defaultdict(int)
        by_model = defaultdict(int)
        for row in rows:
            by_purpose[row["purpose"]] += int(row.get("total_tokens", 0))
            by_model[row["model"]] += int(row.get("total_tokens", 0))
        return {
            "total_call_count": len(rows),
            "total_prompt_tokens": sum(int(r.get("prompt_tokens", 0)) for r in rows),
            "total_completion_tokens": sum(int(r.get("completion_tokens", 0)) for r in rows),
            "total_tokens": sum(int(r.get("total_tokens", 0)) for r in rows),
            "total_estimated_cost_usd": sum(float(r.get("estimated_cost_usd", 0.0)) for r in rows),
            "tokens_by_purpose": dict(by_purpose),
            "tokens_by_model": dict(by_model),
            "fallback_count": sum(1 for r in rows if r.get("fallback_used")),
            "schema_fail_count": sum(1 for r in rows if not r.get("schema_valid", True)),
            "unsafe_proposal_count": sum(1 for r in rows if r.get("unsafe_proposal_detected")),
        }
