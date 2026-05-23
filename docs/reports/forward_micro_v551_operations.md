# ASTT V5.5.1 2주 Live Micro 데이터 축적 운영표

V5.5.1은 실제 주문이 아니라 PAPER forward 검증 단계다. 목표는 초봉/체결/호가 데이터가 충분할 때 micro entry와 micro exit이 실제로 의미가 있는지 확인하는 것이다.

## Day 1
- 5분 smoke session 실행
- 60분 recording 실행
- forward micro report 생성

## Day 2~5
- 하루 1~2회 60분 recording
- 데이터 품질 감사 실행
- write failure, event gap, orderbook 누락 수정

## Day 6~10
- 변동성 큰 시간대 recording
- 09:00 전후 recording
- 22:30 전후 recording

## Day 11~14
- accumulated sessions validation
- cost survival test
- forward micro HTML report 생성

## 목표 기준
- 총 recording time >= 20시간
- GOOD/PARTIAL 거래 >= 30건
- UNAVAILABLE 거래 비중 < 20%
- realistic_1 비용 조건에서 PF >= 1.1 확인

조건을 만족하지 못하면 실전 전환은 금지한다.
