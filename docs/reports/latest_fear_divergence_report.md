# ASTT V4 공포 소진 다이버전스 검증 리포트

## 1. 전략 개요
급락 후 가격은 낮은 저점을 만들지만 공포 압력이 약해지는 구간을 찾고, 볼린저 하단 내부 복귀와 지지/추세/이평 맥락을 확인합니다.

## 2. VIX 다이버전스 → 코인 공포 오실레이터
VIX Fix, 변동성 공포, 거래량 패닉을 합성해 0~100 공포 점수를 만듭니다.

## 3. 5분봉 기준 검증 결과
- entry_count: 0
- win_rate: 0.00%
- profit_factor: 0.0000
- account_return_pct: 0.0000%
- max_drawdown_pct: 0.0000%
- consecutive_loss_max: 0

## 4. 이평선/매물대/추세선 결합 효과
V4 score는 divergence, bollinger re-entry, body zone, trendline, MA, liquidity를 합산합니다.

## 5. Skeptic Guard가 막은 신호
- skeptic_reject_count: 0
- candidate_count: 0

## 6. V3와 비교
- 판정: V4_INSUFFICIENT_SAMPLE

## 7. 50만 원 시드 기준 실제 주문금액 손익
- total_order_pnl_krw: 0원
- account_return_pct: 0.0000%

## 8. 통과/실패 원인
- sweep best: {'status': 'NO_VALID_FEAR_DIVERGENCE_CONFIG'}

## 9. 실전 전환 판정
- LIVE_NOT_ALLOWED

## 10. 다음 실험
- V4 표본이 30회 미만이면 실전 판단을 금지하고 조건 완화/기간 확장 검증을 먼저 한다.
- 유효 V4 설정이 없으면 divergence/reentry/support 임계값을 분리해 민감도 실험을 추가한다.
- V3와의 우열 판단 전에 V4 이벤트 표본을 늘린다.
- V4.1에서 상단 밴드 익절, 1분봉, 15분봉, 청산 방식을 분리 실험한다.
