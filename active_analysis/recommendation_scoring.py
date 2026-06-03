from __future__ import annotations

from active_analysis.analysis_trigger_schema import AnalysisRecommendation


def recommendation(
    recommendation_id: str,
    trigger_type: str,
    severity: str,
    confidence: float,
    expected_benefit: str,
    risk_of_overfit: str = "MEDIUM",
    data_sufficiency: str = "PARTIAL",
    required_followup: str = "manual review",
    allowed_action: str = "REPORT_ONLY",
) -> dict:
    if allowed_action in {"AUTO_ACTIVE_CHANGE", "LIVE_ORDER_ENABLE", "REAL_TRADE_EXECUTION"}:
        raise ValueError(f"forbidden allowed_action: {allowed_action}")
    return AnalysisRecommendation(
        recommendation_id=recommendation_id,
        trigger_type=trigger_type,
        severity=severity,
        confidence=confidence,
        expected_benefit=expected_benefit,
        risk_of_overfit=risk_of_overfit,
        data_sufficiency=data_sufficiency,
        required_followup=required_followup,
        allowed_action=allowed_action,
    ).to_dict()
