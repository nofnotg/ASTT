from execution.hold_time_sweep_runner import run_hold_time_sweep


def test_hold_time_sweep_is_research_only():
    wait = {"rows": [{"post_60s_mfe_pct": 0.4, "post_60s_mae_pct": -0.1, "best_mfe_pct": 0.5, "worst_mae_pct": -0.2}]}
    result = run_hold_time_sweep(wait, [60])
    assert result["rows"][0]["target_hit_rate"] == 1.0
    assert result["included_in_live_readiness"] is False
