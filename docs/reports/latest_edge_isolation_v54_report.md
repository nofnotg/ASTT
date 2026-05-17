# ASTT V5.4 Edge Isolation & Strategy Simplification Report

## 1. V5.3 Failure Summary
V5.3 mixed MTF, zone, target, runner, allocation, and compounding. The result was LIVE_NOT_ALLOWED. V5.4 disables full_seed, grade allocation, runner, and compounding for the base comparison.

## 2. Strategy Isolation
| Strategy | Entry | Win Rate | PF | Expectancy | MDD | Consecutive Loss |
|---|---:|---:|---:|---:|---:|---:|
| MTF_ONLY | 175 | 43.43% | 0.8341 | -0.0543% | -0.3157% | 15 |
| ZONE_ONLY | 175 | 43.43% | 0.8341 | -0.0543% | -0.3157% | 15 |
| MTF_PLUS_ZONE | 175 | 43.43% | 0.8341 | -0.0543% | -0.3157% | 15 |

## 3. Exit Model Compare
| Exit Model | Entry | Win Rate | PF | Avg Win | Avg Loss | Expectancy |
|---|---:|---:|---:|---:|---:|---:|
| FIXED_RR_1_0 | 105 | 45.71% | 0.7726 | 0.5452% | -0.6273% | -0.0733% |
| FIXED_RR_1_2 | 105 | 45.71% | 0.8973 | 0.6332% | -0.6273% | -0.0331% |
| FIXED_RR_1_5 | 105 | 45.71% | 0.9987 | 0.7047% | -0.6273% | -0.0004% |
| ZONE_TARGET_FULL_EXIT | 105 | 42.86% | 0.8552 | 0.6893% | -0.6363% | -0.0500% |
| TP1_BREAK_EVEN | 105 | 37.14% | 0.6451 | 0.5603% | -0.6273% | -0.1145% |

## 4. Module Ablation
| Module Stack | Entry | PF | Expectancy | MDD |
|---|---:|---:|---:|---:|
| BASE_TRIGGER_ONLY | 525 | 0.8341 | -0.0543% | -0.9472% |
| BASE+DAILY | 525 | 0.8341 | -0.0543% | -0.9472% |
| BASE+H4 | 525 | 0.8341 | -0.0543% | -0.9472% |
| BASE+DAILY+H4 | 525 | 0.8341 | -0.0543% | -0.9472% |
| BASE+ZONE | 350 | 0.8341 | -0.0543% | -0.6315% |
| BASE+DAILY+H4+ZONE | 350 | 0.8341 | -0.0543% | -0.6315% |
| BASE+DAILY+H4+ZONE+BTC | 350 | 0.8341 | -0.0543% | -0.6315% |
| BASE+DAILY+H4+ZONE+TARGET | 350 | 0.8341 | -0.0543% | -0.6315% |

## 5. Zone Quality V54
- zone_count: 525
- quality_grade_performance: [{'quality_grade': 'C', 'entry_count': 15, 'win_rate': 0.0, 'expectancy_pct': -0.3838771593090211, 'profit_factor': 0.0}, {'quality_grade': 'REJECT', 'entry_count': 510, 'win_rate': 0.4470588235294118, 'expectancy_pct': -0.044587125202252074, 'profit_factor': 0.8630167129898608}]

## 6. Trade Review Dataset
- review row count: 35
- markdown: docs/reports/trade_review_v54.md
- csv: docs/reports/trade_review_v54.csv

## 7. Live Readiness
LIVE_NOT_ALLOWED

## 8. Insights
- No isolated strategy has enough PF and sample quality to claim edge.
- V5.4 intentionally does not output MICRO_LIVE_READY.
