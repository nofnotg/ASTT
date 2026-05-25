from __future__ import annotations


def analyze_setup_context_improvement(journal: list[dict]) -> list[dict]:
    rows = []
    for setup in sorted({row["setup_type"] for row in journal}):
        base = [row for row in journal if row["setup_type"] == setup]
        combined = [row for row in base if row["strategy"] == "COMBINED_VOLUME_ICT"]
        base_return = sum(row["pnl_krw"] for row in base)
        combined_return = sum(row["pnl_krw"] for row in combined)
        rows.append({
            "setup": setup,
            "base_return_krw": base_return,
            "with_daddy_context_krw": combined_return,
            "improvement_krw": combined_return - base_return,
            "decision": "STRENGTHEN" if combined_return > 0 else "KEEP",
        })
    return rows
