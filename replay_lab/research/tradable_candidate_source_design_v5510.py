from __future__ import annotations

import json
from pathlib import Path

from features.tradable_candidate_sources import TRADABLE_SOURCES
from replay_lab.paths import REPLAY_STORE_DIR


def design_tradable_candidate_sources_v5510(tradable_traces: str | Path) -> dict:
    trace_path = Path(tradable_traces) / "tradable_traces.json"
    trace_count = len(json.loads(trace_path.read_text(encoding="utf-8")).get("traces", [])) if trace_path.exists() else 0
    result = {
        "trace_count": trace_count,
        "source_specs": [{"source": source, "research_mode": True, "real_order_enabled": False} for source in TRADABLE_SOURCES],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
    }
    out = REPLAY_STORE_DIR / "tradable_trace" / "tradable_source_design.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
