from __future__ import annotations

from validation.causal_defense_auditor import audit_causal_defense


def test_causal_defense_auditor_passes_clean_sample():
    payload = {
        "scenario_count": 1,
        "scenarios": [
            {
                "scenario": "BASELINE",
                "annotated_trade_sample": [
                    {
                        "trade_id": "t1",
                        "feature_cutoff_time": "2025-01-01 09:00:00",
                        "decision_time": "2025-01-01 09:00:00",
                        "entry_time": "2025-01-01 09:00:00",
                        "used_future_data": False,
                        "rolling_trades_used": 0,
                    }
                ],
                "equity_curve_sample": [{"time": "2025-01-01 10:00:00", "equity": 501000}],
            }
        ],
    }

    audit = audit_causal_defense(payload)

    assert audit["overall_status"] == "PASS"
