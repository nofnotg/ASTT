from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AnalysisRecommendation:
    recommendation_id: str
    trigger_type: str
    severity: str
    confidence: float
    expected_benefit: str
    risk_of_overfit: str
    data_sufficiency: str
    required_followup: str
    allowed_action: str
    manual_approval_required: bool = True
    active_change_applied: bool = False
    live_order_allowed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)
