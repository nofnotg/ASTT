from __future__ import annotations


def summarize_persona_calibration(persona_scores) -> dict:
    if persona_scores is None or persona_scores.empty:
        return {}
    return persona_scores.groupby("persona")["score"].mean().to_dict()
