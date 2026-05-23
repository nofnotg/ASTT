# ASTT V5.5.3 Upbit Real API Report

## 한눈에 보는 결론
- 실제 업비트 WebSocket 연결: True
- Mock 데이터 readiness 제외: True
- GOOD/PARTIAL 초봉 window: 18
- ENTER만 손익 집계: True
- WAIT/CANCEL 오류 경고: OK
- realistic_1 PF: 0.0
- 실전 전환 판단: LIVE_NOT_ALLOWED

초봉은 전체 기간을 모두 긁는 데이터가 아니라, 후보 종목의 진입 전후 흐름을 확인하는 실행 데이터입니다.

초봉 데이터가 없다는 것은 API 실패가 아니라 해당 초에 체결이 없었다는 뜻일 수 있습니다.

Mock 데이터는 시스템 테스트용이며 실전성 판단에 사용하지 않습니다.

WAIT/CANCEL은 실제 매수하지 않은 후보이므로 손익에 넣으면 안 됩니다.

0.05% 비용 조건에서 수익성이 무너지면 초단타 실전은 금지입니다.
