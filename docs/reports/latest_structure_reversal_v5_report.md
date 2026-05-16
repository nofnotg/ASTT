# ASTT V5 다중 시간봉 구조반전 검증 리포트

## 1. V5 전략 개요
V5는 주봉/일봉/4H 상위 구조를 먼저 확인하고 1H/15M 셋업, 5M/1M 트리거, Risk Gate를 통과한 경우에만 PAPER 진입하는 구조반전 전략이다.

## 2. Small Seed Daily 결과
- entry_count: 38
- win_rate: 50.00%
- profit_factor: 1.4546
- account_return_pct: 0.0581%
- max_drawdown_pct: -0.0314%
- consecutive_loss_max: 3

## 3. Sweep 최고 설정
```json
{
  "entries": 35,
  "entry_count": 35,
  "entry_days": 35,
  "hold_days": 0,
  "wins": 22,
  "losses": 13,
  "win_rate": 0.6285714285714286,
  "avg_signal_pnl_pct": 0.23896668758537207,
  "avg_net_signal_pnl_pct": 0.23896668758537207,
  "avg_order_pnl_krw": 23.89666875853721,
  "total_order_pnl_krw": 836.3834065488023,
  "account_return_pct": 0.16727668130976048,
  "max_drawdown_pct": -0.04296774710788644,
  "profit_factor": 2.6802053020028125,
  "avg_win_pct": 0.6064408368503272,
  "avg_loss_pct": -0.3829126419399366,
  "loss_day_count": 13,
  "consecutive_loss_max": 4,
  "status": "PAPER_MORE_REQUIRED",
  "weekly_min_score": 50,
  "daily_min_score": 55,
  "h4_min_score": 50,
  "v5_min_score": 70,
  "risk_reward_min": 1.0,
  "use_ichimoku": false,
  "mode": "small_seed_daily",
  "exit_mode": "fixed_rr",
  "max_daily_entries": 1,
  "max_hold_minutes": 120,
  "strategy_types": [
    "TREND_CONTINUATION_PULLBACK",
    "FAILED_BREAKDOWN_RECLAIM",
    "BOTTOM_REVERSAL"
  ]
}
```

## 4. MTF Context Compare
- best_context_stack: Daily + 4H

## 5. V3/V4.1/V5 비교
- verdict: V5_OUTPERFORMS_PRIOR

## 6. 실전 전환 판정
- MICRO_LIVE_READY

## 7. 인사이트
- MTF context best stack은 Daily + 4H이다. 이 값이 No MTF보다 낫지 않다면 상위 필터는 후보 품질보다 후보 축소 효과가 더 컸다는 뜻이다.
- V3/V4.1/V5 비교 판정은 V5_OUTPERFORMS_PRIOR이다.
- Weekly Sniper는 표본이 적어도 연속손실을 낮추는지 확인하는 보조 축으로 유지한다.
