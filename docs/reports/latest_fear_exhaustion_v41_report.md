# ASTT V4.1 Relaxed Fear Exhaustion 검증 리포트

## 1. V4 실패 원인 요약
V4는 정통 공포 다이버전스 조건이 너무 엄격해 후보가 0개에 가까웠다. V4.1은 수익률을 증명하기 전에 후보가 어느 조건에서 사라지는지 보기 위한 병목 진단 버전이다.

## 2. V4.1 완화 로직
- 급락 이벤트: 최근 고점 대비 저점 하락률을 본다.
- 저점 구조: 정통 lower low뿐 아니라 low retest도 허용한다.
- 공포 둔화: fear_score, volume_panic, volatility_fear 중 하나만 둔화해도 통과 가능하다.
- 볼린저 복귀: 하단 밴드 밖 매수는 금지하고 내부 복귀 후만 후보로 본다.
- 최소 지지: 몸통 매물대, 추세선, 이전 저점, MA30 목표 공간, 볼린저 중심선 공간 중 1개 이상을 요구한다.

## 3. 1m vs 5m 최고 결과
- best_timeframe: 5m
- entry_count: 36
- win_rate: 47.22%
- profit_factor: 0.778
- account_return_pct: -0.0621%

## 4. Funnel Report
| 단계 | count |
| --- | ---: |
| 1m / total_bars | 291,052 |
| 1m / drop_event_count | 20,578 |
| 1m / low_retest_or_lower_low_count | 20,450 |
| 1m / fear_cooling_count | 10,259 |
| 1m / bollinger_reentry_count | 8,367 |
| 1m / min_support_context_count | 4,517 |
| 1m / v41_score_pass_count | 1,154 |
| 1m / skeptic_pass_count | 617 |
| 1m / skeptic_warn_count | 0 |
| 1m / skeptic_reject_count | 537 |
| 1m / final_entry_count | 44 |
| 5m / total_bars | 77,599 |
| 5m / drop_event_count | 3,108 |
| 5m / low_retest_or_lower_low_count | 3,052 |
| 5m / fear_cooling_count | 1,515 |
| 5m / bollinger_reentry_count | 1,193 |
| 5m / min_support_context_count | 900 |
| 5m / v41_score_pass_count | 387 |
| 5m / skeptic_pass_count | 180 |
| 5m / skeptic_warn_count | 0 |
| 5m / skeptic_reject_count | 207 |
| 5m / final_entry_count | 44 |

## 5. Skeptic Guard 진단 결과
- mode: DIAGNOSTIC
- would_block_count: 537
- blocking_applied_count: 0

## 6. 50만 원 시드 기준 손익
- order_krw: 10,000원
- total_order_pnl_krw: -72원
- account_return_pct: -0.0143%

## 7. V4 vs V4.1 비교
- 판정: V41_REJECTED

## 8. 실전 전환 판정
- LIVE_NOT_ALLOWED

## 9. 다음 실험 제안
- 수익성 기준이 약하면 상단 밴드 익절보다 먼저 손절/시간청산 조건을 분리 실험한다.
- 퍼널에서 가장 크게 줄어드는 조건을 다음 실험의 1순위 완화 대상으로 둔다.
- Skeptic Guard는 당분간 DIAGNOSTIC으로 유지하고, 표본이 충분해진 뒤 BLOCKING 전환 여부를 판단한다.
- BTC 쇼크 필터와 15분봉 맥락 필터를 추가해 1분봉 노이즈를 줄이는 실험을 분리한다.
