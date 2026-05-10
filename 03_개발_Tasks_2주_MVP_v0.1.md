# 개발 Tasks: 2주 MVP 구축 계획 v0.1

## 전체 원칙

- 2주 안에 완벽한 자동매매를 만들지 않는다.
- 2주 안에 “09:00 후보 탐지 + 페르소나 점수 + 모의투자 + 피드백 저장”을 완성한다.
- 실거래는 기본 비활성화한다.
- 모든 작업은 테스트와 완료 기준을 포함한다.

## Sprint 0: 프로젝트 초기화

### TASK-000. Repository 초기화

**목표**: 실행 가능한 기본 프로젝트 생성.

**작업**
- Python 3.11+ 가상환경 구성
- 폴더 구조 생성
- `pyproject.toml` 또는 `requirements.txt` 작성
- `.env.example` 작성
- `README.md` 작성

**완료 기준**
- `python -m app.main` 실행 가능
- `pytest` 실행 가능
- API 키 없이도 모의 모드 실행 가능

---

## Sprint 1: 데이터 수집과 저장

### TASK-101. 업비트 Public Market Collector

**목표**: 업비트 KRW 마켓 목록, 현재가, 캔들 데이터를 수집한다.

**작업**
- `adapters/upbit_client.py`
- `data/collectors.py`
- 1m/5m/15m/1h/1d 캔들 수집 함수
- Rate limit 대응: 요청 간격, 429 처리, 재시도 제한

**완료 기준**
- KRW 마켓 목록 수집 성공
- 1분봉 200개 이상 저장 가능
- 누락/중복 캔들 검사 함수 존재

### TASK-102. SQLite/Parquet 저장소

**목표**: OHLCV와 신호 데이터를 저장한다.

**작업**
- `data/storage.py`
- `candles`, `persona_scores`, `signals`, `paper_trades` 테이블 생성
- upsert 방식 구현

**완료 기준**
- 동일 캔들 중복 저장 방지
- 신호/거래 로그 조회 가능

### TASK-103. 08:50 후보군 스캐너

**목표**: 거래대금 상위 후보를 08:50에 압축한다.

**작업**
- 거래대금 상위 50개 추출
- 스프레드 과다 종목 제외
- 유의/제외 마켓 설정 파일 적용

**완료 기준**
- 후보 목록 JSON/DB 저장
- 대시보드에서 후보 확인 가능

---

## Sprint 2: Feature Engine

### TASK-201. 몸통 매물대 계산

**목표**: 대량거래 캔들의 몸통 구간을 지지/저항 후보로 추출한다.

**작업**
- `features/body_zone.py`
- 최근 N봉 평균 거래량 대비 RVOL 기준 대량 캔들 정의
- open/close 기준 body_low/body_high 산출

**완료 기준**
- 종목별 상위 매물대 3개 반환
- 매물대 구간과 현재가 거리 계산

### TASK-202. R/S Flip 후보 탐지

**목표**: 저항 돌파 직전/직후 후보를 탐지한다.

**작업**
- 돌파 전 대기 구간
- 돌파 후 지지 확인 구간
- 종가 기준 이탈 여부 계산

**완료 기준**
- `PRE_BREAKOUT`, `BREAKOUT`, `RETEST`, `FAILED` 상태 반환

### TASK-203. Rezo 실시간 수급 지표

**목표**: RVOL, 거래량 가속도, VWAP, CVD 기초값을 계산한다.

**작업**
- `features/rvol.py`
- `features/vwap.py`
- `features/cvd.py`
- 1분 단위 기초 계산부터 구현

**완료 기준**
- 후보 종목별 RVOL, VWAP 위치, CVD 방향 반환

### TASK-204. 레짐/시장 필터

**목표**: BTC 및 시장 전체 흐름을 점수화한다.

**작업**
- BTC 1m/5m/1h 수익률
- KRW 마켓 상승 종목 비율
- 거래대금 상위 종목 방향성

**완료 기준**
- `BULLISH`, `NEUTRAL`, `BEARISH`, `PANIC` 중 하나 반환

---

## Sprint 3: 페르소나 엔진

### TASK-301. Persona Base Interface

**목표**: 모든 페르소나가 같은 입력/출력 구조를 따르게 한다.

**작업**
- `personas/base.py`
- Pydantic 모델 정의
- score, decision, reasons, warnings, veto, payload 표준화

**완료 기준**
- 모든 페르소나가 동일한 schema 반환

### TASK-302. 매기 구현

**목표**: 09:00 후보 사전 선별과 맥점 가격대를 산출한다.

**작업**
- 몸통 매물대 점수
- 목표 공간 점수
- R/S Flip 상태 점수
- 이평선 위치 점수
- 전일 고점 근접 점수

**완료 기준**
- market별 `maggie_score`, entry_zone, stop_loss, target 반환

### TASK-303. Rezo 구현

**목표**: 실제 수급 점화 여부를 판단한다.

**작업**
- RVOL 점수
- 거래량 가속도 점수
- VWAP 위/아래 점수
- CVD 방향 점수
- 호가 스프레드 점수

**완료 기준**
- `rezo_score >= 80`이면 strong_flow=true 반환

### TASK-304. CostA 구현

**목표**: 분할매수와 평균단가 리스크를 계산한다.

**작업**
- buy_plan 설정 읽기
- 단계별 평균단가 계산
- 탈출가 계산
- 종목별 최대 노출 계산
- 자금 부족/과노출 경고

**완료 기준**
- 1/2/3차 매수 플랜별 평균단가와 탈출가 반환
- max_exposure 초과 시 veto=true

### TASK-305. Iris 구현

**목표**: 최종 리스크 거부권을 구현한다.

**작업**
- 손익비 계산
- 일일 손실 한도
- 연속 손절 한도
- 중복 포지션 차단
- 스프레드/슬리피지 기준

**완료 기준**
- veto 사유가 명확히 저장됨
- Iris veto 시 Final Score와 무관하게 진입 금지

### TASK-306. Mr.K 구현

**목표**: 초기에는 수동/반자동 시장 모드 입력으로 구현한다.

**작업**
- `AGGRESSIVE`, `NEUTRAL`, `DEFENSIVE` 수동 선택
- 시장 브리핑 메모 저장
- 가중치에 반영

**완료 기준**
- 대시보드에서 오늘의 운용 모드 변경 가능

---

## Sprint 4: 토론·의사결정

### TASK-401. Debate Engine

**목표**: 페르소나 결과를 모아 최종 결정을 만든다.

**작업**
- 독립 분석 결과 수집
- 반박 메시지 생성
- 가중 점수 계산
- veto 적용

**완료 기준**
- Final Score와 decision 저장
- 진입/관찰/제외 사유가 3줄 이상 생성

### TASK-402. Strategy 09:00 Runner

**목표**: 08:50~09:30 흐름을 자동 실행한다.

**작업**
- 08:50 후보 스캔
- 09:00 수급 감시
- 09:03~09:10 진입 판단
- 09:30 신규 진입 종료

**완료 기준**
- 지정 시간대에 모의 신호 자동 생성

---

## Sprint 5: 모의투자와 대시보드

### TASK-501. Paper Trader

**목표**: 실제 주문 없이 가상 진입/청산을 기록한다.

**작업**
- 가상 포지션 생성
- 목표가/손절가/시간청산
- 수수료/슬리피지 보수 적용

**완료 기준**
- paper_trades에 진입/청산/손익 저장

### TASK-502. Streamlit Dashboard

**목표**: 후보와 페르소나 판단을 한 화면에서 본다.

**화면**
- 후보군 대시보드
- 페르소나 점수판
- 토론 로그
- 모의 포지션
- 성과 리포트

**완료 기준**
- `streamlit run dashboard/streamlit_app.py` 실행 가능

---

## Sprint 6: 피드백과 리포트

### TASK-601. 거래 결과 분석

**목표**: 승/패 원인을 페르소나별로 추적한다.

**작업**
- score bucket별 성과
- 매기 80+ vs 60 이하 비교
- Rezo 80+ vs 60 이하 비교
- Iris veto 회피 성과 분석

**완료 기준**
- 일간 리포트 자동 생성

### TASK-602. 버전 관리

**목표**: 파라미터 변경 전후 성과를 비교한다.

**작업**
- config version 저장
- persona_weights version 저장
- 리포트에 version 표시

**완료 기준**
- 특정 거래가 어떤 버전에서 발생했는지 추적 가능

---

## 2주 일정표

| 일자 | 목표 |
|---:|---|
| Day 1 | Repo, 저장소, 업비트 캔들 수집 |
| Day 2 | 후보 스캐너, DB 저장 |
| Day 3 | 몸통 매물대, R/S Flip |
| Day 4 | RVOL, VWAP, CVD 기초 |
| Day 5 | 매기, Rezo 구현 |
| Day 6 | CostA, Iris 구현 |
| Day 7 | Debate Engine, 09:00 Runner |
| Day 8 | Paper Trader |
| Day 9 | Dashboard v0 |
| Day 10 | 결과 리포트, 버전 관리 |
| Day 11 | 단위 테스트, 데이터 누락 검사 |
| Day 12 | 09:00 모의 리허설 |
| Day 13 | 백테스트/리플레이 테스트 |
| Day 14 | 1차 운영 리포트 및 v0.2 작업 정의 |

## Definition of Done

- 모든 핵심 모듈은 단위 테스트 1개 이상 포함
- 09:00 흐름이 수동 개입 없이 실행 가능
- 실거래 버튼/기능은 기본 비활성화
- 모의거래 결과와 페르소나 점수가 DB에 저장됨
- 오류 발생 시 거래 판단 중단

---

## 참고자료
- 업비트 거래 데이터 기준 시간: https://support.upbit.com/hc/ko/articles/900006049666-%EA%B1%B0%EB%9E%98-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EA%B8%B0%EC%A4%80-%EC%8B%9C%EA%B0%84%EC%9D%80-%EC%96%B8%EC%A0%9C%EC%9D%B8%EA%B0%80%EC%9A%94
- 업비트 REST API Best Practice: https://docs.upbit.com/kr/docs/rest-api-best-practice
- 업비트 초(Second) 캔들 조회: https://docs.upbit.com/kr/reference/list-candles-seconds
- 업비트 주문 생성 테스트: https://docs.upbit.com/kr/reference/order-test
- 빗썸 Candlestick REST API: https://apidocs.bithumb.com/v1.2.0/reference/candlestick-rest-api
- 빗썸 주문 요청 API: https://apidocs.bithumb.com/v2.1.0/reference/%EC%A3%BC%EB%AC%B8-%EC%9A%94%EC%B2%AD
- 빗썸 Developer Docs: https://apidocs.bithumb.com/docs/%EB%B9%97%EC%8D%B8-developer-docs
