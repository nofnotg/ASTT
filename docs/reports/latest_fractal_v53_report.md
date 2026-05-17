# ASTT V5.3 Full Validation / Allocation / Zone Reaction / Runner Report

## 1. V5.2 to V5.3 Change Summary
V5.3 does not add a new entry signal. It adds validation speed, allocation diagnostics, stricter zone reaction labels, runner/trailing diagnostics, and wider walk-forward checks.

## 2. Final V5.3 Result
- period: 2026-01-01 ~ 2026-05-15
- entry_count: 35
- win_rate: 42.86%
- profit_factor: 0.3408
- initial_equity_krw: 500,000
- final_equity_krw: 495,936
- equity_return_pct: -0.8129%
- max_drawdown_pct: -0.8129%
- consecutive_loss_max: 3
- full_validation_completed: False

## 3. Cache Benchmark
- cache_hit_rate: 1.0000
- cache_off_time: 0.0439s
- cache_on_time: 0.0865s
- speedup_ratio: 0.51
- full_validation_estimated_time: 25.95s

## 4. Allocation Diagnostic
| Grade | Entry | Win Rate | PF | Avg Alloc | Total PnL | Allocation Alpha |
|---|---:|---:|---:|---:|---:|---:|
| A_PLUS | 1 | 0.00% | 0.0000 | 0.675 | -2,693 | 1,296 |
| A | 1 | 0.00% | 0.0000 | 0.244 | -974 | 3,021 |
| B | 1 | 0.00% | 0.0000 | 0.262 | -94 | 265 |
| C | 32 | 46.88% | 0.8737 | 0.054 | -304 | -623 |
| REJECT | 0 | 0.00% | 0.0000 | 0.000 | 0 | 0 |
| PAPER_ONLY | 0 | 0.00% | 0.0000 | 0.000 | 0 | 0 |

- good_trade_underallocated_count: 15
- bad_trade_overallocated_count: 1
- allocation_alpha_krw: 3,960
- summary: grade_based_helped

## 5. Zone Reaction Validation
- zone_count: 35
- bounce_success_rate: 0.2286
- rejection_success_rate: 0.0000
- breakdown_fail_rate: 0.1714
- no_reaction_rate: 0.4857
- zone_strength_correlation: 0.0733
- validation_passed: False

## 6. Runner / Trailing Sweep
- best_runner_model: AGGRESSIVE_RUNNER
- best_trailing_model: break_even_after_tp1
- best_runner_contribution_krw: 619

## 7. Walk-forward
- window_count: 7
- positive_window_ratio: 0.0000
- avg_test_profit_factor: 0.1876
- median_test_profit_factor: 0.0000
- avg_test_return_pct: -0.1164%
- worst_window_mdd_pct: -0.6175%
- stable: False

## 8. Fixed 10k vs Full Seed vs Grade-Based V53
| Model | Entry | PF | Final Equity | Return % | MDD | Consecutive Loss |
|---|---:|---:|---:|---:|---:|---:|
| fixed_10k | 35 | 0.8414 | 499,840 | -0.0320% | -0.0494% | 3 |
| full_seed | 35 | 0.8316 | 491,538 | -1.6925% | -2.4865% | 3 |
| grade_based_v53 | 35 | 0.3408 | 495,936 | -0.8129% | -0.8129% | 3 |

## 9. Live Readiness
LIVE_NOT_ALLOWED

## 10. Insights
- Full top50 coverage was not proven from the available V5.2 seed, so MICRO_LIVE_READY is blocked.
- Grade-based allocation added defensive alpha versus full-seed counterfactual in this replay sample.
- Zone reaction validation is not strong enough yet; zone strength needs more discriminating labels.
- Runner/trailing produced positive contribution in the diagnostic sweep, but it still needs walk-forward confirmation.
- Walk-forward is not stable; this is the main blocker for any live transition.
- Best allocation model in the current comparison: fixed_10k.
