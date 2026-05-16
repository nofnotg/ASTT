from replay_lab.research.fear_exhaustion_funnel_v41 import FUNNEL_KEYS, bottleneck_stage


def test_funnel_counts_are_monotonic():
    funnel = {
        "total_bars": 100,
        "drop_event_count": 50,
        "low_retest_or_lower_low_count": 30,
        "fear_cooling_count": 20,
        "bollinger_reentry_count": 10,
        "min_support_context_count": 8,
        "v41_score_pass_count": 6,
        "skeptic_pass_count": 3,
        "skeptic_warn_count": 2,
        "skeptic_reject_count": 1,
        "final_entry_count": 5,
    }
    ordered = [funnel[key] for key in FUNNEL_KEYS if key not in {"skeptic_pass_count", "skeptic_warn_count", "skeptic_reject_count"}]
    assert ordered == sorted(ordered, reverse=True)
    assert bottleneck_stage(funnel) in funnel
