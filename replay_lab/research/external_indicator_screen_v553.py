from __future__ import annotations

from research_external.external_indicator_taxonomy import build_indicator_taxonomy


def screen_external_indicators_v553() -> dict:
    taxonomy = build_indicator_taxonomy()
    groups = sorted({row["group"] for row in taxonomy})
    return {"indicator_count": len(taxonomy), "indicator_groups": groups, "taxonomy": taxonomy}
