# ASTT V3 소액 시드 자동매매 검증 리포트

## 1. 최종 요약
- 기간: 2026-01-01 ~ 2026-05-15
- 시드: 500,000원
- 주문금액: 10,000원
- 진입 수: 134
- 승률: 38.06%
- 실제 주문금액 손익: -1,890원
- 계좌 성장률: -0.3781%
- MDD: -0.4695%
- Profit Factor: 0.7012
- 실전 전환 판정: LIVE_NOT_ALLOWED

## 2. 거래 수익률 vs 실제 주문금액 손익
1만 원 주문에서 +1%는 100원이며, 50만 원 계좌 기준으로는 +0.02%입니다. 이 리포트는 거래 수익률과 계좌 성장률을 분리합니다.

## 3. Threshold Sweep 결과
- 상태: NO_VALID_THRESHOLD
- 설정: final=None, setup=None, trigger=None, confidence=None
- entry_count: 0
- account_return_pct: 0.0000
- max_drawdown_pct: 0.0000

## 4. 시간창별 기대값
- 17:00: entry=3, account=0.0112%, score=1998.311
- 16:30: entry=3, account=0.0064%, score=1998.306
- 20:30: entry=3, account=0.0064%, score=65.195
- 18:00: entry=3, account=0.0077%, score=22.217
- 12:00: entry=3, account=0.0058%, score=18.599
- 11:30: entry=3, account=0.0067%, score=15.315
- 17:30: entry=3, account=0.0013%, score=12.270
- 06:00: entry=132, account=0.5609%, score=10.061
- 05:30: entry=132, account=0.3450%, score=8.393
- 01:00: entry=134, account=0.2728%, score=7.862

## 5. PreOpen vs Confirmed
- 더 적합한 모드: confirmed
- PreOpen: {'mode': 'preopen', 'entries': 134, 'entry_count': 134, 'entry_days': 134, 'hold_days': 0, 'wins': 47, 'losses': 66, 'win_rate': 0.35074626865671643, 'avg_signal_pnl_pct': -0.1984579533664797, 'avg_net_signal_pnl_pct': -0.1984579533664797, 'avg_order_pnl_krw': -19.845795336647967, 'total_order_pnl_krw': -2659.3365751108277, 'account_return_pct': -0.5318673150221654, 'max_drawdown_pct': -0.5830580074705334, 'profit_factor': 0.600634030440504, 'avg_win_pct': 0.8509701532009493, 'avg_loss_pct': -1.0089236810841349, 'loss_day_count': 66, 'consecutive_loss_max': 6, 'false_breakout_loss_count': 34, 'missed_big_move_count': 12, 'time_exit_count': 82}
- Confirmed: {'mode': 'confirmed', 'entries': 134, 'entry_count': 134, 'entry_days': 134, 'hold_days': 0, 'wins': 51, 'losses': 69, 'win_rate': 0.3805970149253731, 'avg_signal_pnl_pct': -0.14107421987203844, 'avg_net_signal_pnl_pct': -0.14107421987203844, 'avg_order_pnl_krw': -14.107421987203843, 'total_order_pnl_krw': -1890.3945462853148, 'account_return_pct': -0.37807890925706295, 'max_drawdown_pct': -0.4694704792721964, 'profit_factor': 0.7011864736976379, 'avg_win_pct': 0.869792295936525, 'avg_loss_pct': -0.9168601819654478, 'loss_day_count': 69, 'consecutive_loss_max': 6, 'false_breakout_loss_count': 32, 'missed_big_move_count': 10, 'time_exit_count': 84}

## 6. 다음 개발 과제
- Threshold Sweep에서 유효 후보가 없으므로 EntryGate 완화 범위를 더 넓혀 재실험한다.
- 계좌 성장률이 양수가 아니므로 MICRO LIVE 전환은 금지하고 PAPER 검증을 지속한다.
- Confirmed 모드가 더 적합하면 09:03 확인 후 진입을 기본 후보로 둔다.
- 상위 시간창 3개만 대상으로 2주 Live Paper 검증 시나리오를 만든다.
- 시간창 랭킹 상단에 표본 30회 미만 구간이 있으면 참고 후보로만 보고, 신뢰 후보는 entry_count 30회 이상으로 제한한다.
