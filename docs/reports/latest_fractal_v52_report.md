# ASTT V5.2 Fractal MTF + BTC Dominance + Zone Target + Full-Seed Compounding 검증 리포트

## 1. V5.2 전략 개요
V5.2는 V5의 MTF 신호 위에 BTC regime, zone target space, dynamic exit, full-seed position sizing, compounding portfolio를 얹은 PAPER 전용 검증이다.

## 2. Full-Seed Compounding 결과
- entry_count: 35
- win_rate: 48.57%
- profit_factor: 1.1227
- initial_equity_krw: 500,000
- final_equity_krw: 500,211
- equity_return_pct: 0.0422%
- max_drawdown_pct: -0.2901%
- consecutive_loss_max: 3

## 3. Zone Engine 검증
- zone_count: 68
- demand_zone_bounce_rate: 0.7318
- supply_zone_rejection_rate: 0.6653
- zone_target_hit_rate: 0.6098

## 4. Walk-forward
- window_count: 1
- avg_test_profit_factor: 0.4961
- avg_test_return_pct: -0.0235
- stable: False

## 5. 실전 전환 판정
- LIVE_NOT_ALLOWED

## 6. 인사이트
- Zone validation은 현재 OHLCV proxy 기반이며, 추후 실제 반응 라벨을 보강해야 한다.
- 현재 비교에서 가장 나은 allocation model은 full_seed이다.
- walk-forward 안정성이 부족하거나 전체 window가 부족하면 MICRO_LIVE_READY 금지다.
