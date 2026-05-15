import pandas as pd

from replay_lab.research.threshold_sweep_v3 import ThresholdConfigV3, evaluate_threshold_configs, generate_threshold_configs, select_best_threshold


def test_generate_threshold_configs_cross_product():
    configs = generate_threshold_configs()
    assert len(configs) == 4 * 4 * 4 * 3
    assert configs[0].final_score == 70


def test_threshold_sweep_reports_no_valid_candidate_when_entries_are_sparse():
    candidates = pd.DataFrame(
        [
            {
                "date_kst": "2026-01-01",
                "market": "KRW-BTC",
                "final_score": 90,
                "setup_score": 90,
                "trigger_score": 90,
                "entry_gate_confidence": 90,
                "risk_decision": "PASS",
                "gross_signal_pnl_pct": 1.0,
                "net_signal_pnl_pct": 1.0,
                "order_pnl_krw": 100.0,
            }
        ]
    )
    rows = evaluate_threshold_configs(candidates, [ThresholdConfigV3(70, 65, 65, 50)], capital_krw=500000)
    assert rows[0]["entry_count"] == 1
    assert select_best_threshold(rows)["status"] == "NO_VALID_THRESHOLD"
