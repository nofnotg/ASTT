# Cursor/Codex 작업 지시문 v0.1

아래 지시문은 빠른 MVP 구축을 위해 그대로 붙여넣어 사용할 수 있다. 각 작업은 반드시 기존 파일 구조를 먼저 확인한 뒤 최소 변경으로 진행한다.

## 공통 지시문 헤더

```text
당신은 멀티 페르소나 투자 앱 MVP를 구현하는 시니어 Python 개발자다.
목표는 실전 자동매매가 아니라 09:00 후보 탐지, 페르소나 점수화, 모의투자, 피드백 저장이 가능한 검증용 MVP를 빠르게 구축하는 것이다.

금지:
- 실전 주문을 기본 활성화하지 말 것
- API Key를 코드에 하드코딩하지 말 것
- 출금 권한을 요구하지 말 것
- Iris veto를 우회하지 말 것
- 손절/리스크 저장 없이 진입 신호를 만들지 말 것

필수:
- 모든 핵심 함수는 단위 테스트를 포함할 것
- 모든 판단 결과는 DB에 저장할 것
- 오류 발생 시 진입 판단을 중단할 것
- 함수 출력은 Pydantic 모델 또는 명확한 dict schema를 따를 것
```

## Prompt 1: 프로젝트 골격 생성

```text
프로젝트 루트에 아래 구조를 생성하라.

multi-persona-investment-app/
  app/
  adapters/
  data/
  features/
  personas/
  decision/
  simulation/
  execution/
  feedback/
  dashboard/
  tests/
  config/
  data_store/

requirements.txt, .env.example, README.md를 작성하라.
Python 3.11 기준으로 FastAPI, pandas, numpy, pydantic, apscheduler, streamlit, pytest, python-dotenv, requests, websockets를 포함하라.
실전 주문 기능은 stub만 만들고 기본 비활성화하라.
```

## Prompt 2: 업비트 데이터 수집기

```text
adapters/upbit_client.py와 data/collectors.py를 구현하라.
기능:
1. KRW 마켓 목록 조회
2. 1분봉/5분봉/15분봉/1시간봉/일봉 조회
3. 요청 제한 대응용 간단한 rate limiter
4. 429 응답 시 재시도하지 말고 해당 그룹 호출을 중단 후 오류를 반환
5. candles 테이블에 저장 가능한 dict 리스트 반환

테스트:
- API 호출을 mock 처리하여 정상 응답 parsing 테스트
- 빈 응답 처리 테스트
- 중복 캔들 제거 테스트
```

## Prompt 3: Feature Engine

```text
features/ 아래에 body_zone.py, rvol.py, vwap.py, cvd.py, regime.py를 구현하라.
각 함수는 pandas DataFrame을 입력받고 계산 결과 dict를 반환한다.

필수 기능:
- 대량거래 몸통 매물대 계산
- RVOL 계산
- VWAP 계산
- 단순 CVD 계산
- BTC 기반 레짐 판정

테스트:
- 임의 OHLCV fixture로 계산값 검증
- NaN/빈 데이터 입력 시 안전하게 실패
```

## Prompt 4: 페르소나 엔진

```text
personas/base.py에 PersonaResult 모델을 정의하라.
그 다음 personas/mr_k.py, maggie.py, rezo.py, costa.py, iris.py를 구현하라.

각 페르소나는 analyze(context) -> PersonaResult를 반환한다.

PersonaResult 필드:
- persona
- market
- timestamp
- score: 0~100
- decision: ENTER/WATCH/REJECT
- confidence
- reasons: list[str]
- warnings: list[str]
- veto: bool
- payload: dict

Iris는 veto=true를 반환할 수 있으며, 이 경우 최종 진입은 금지되어야 한다.
```

## Prompt 5: Debate Engine

```text
decision/debate_engine.py를 구현하라.
입력: PersonaResult 리스트, persona_weights.yaml
출력: FinalDecision

규칙:
- Iris veto=true이면 decision=REJECT
- Final Score는 가중 평균
- 85 이상 ENTER_CANDIDATE
- 70~84 WATCH
- 70 미만 REJECT
- 최종 사유를 3개 이상 생성

테스트:
- Iris veto 우선권 테스트
- 가중 평균 계산 테스트
- 누락 페르소나 처리 테스트
```

## Prompt 6: Paper Trader

```text
simulation/paper_trader.py를 구현하라.
실제 주문 없이 가상 진입/청산을 기록한다.

기능:
- FinalDecision이 ENTER_CANDIDATE일 때 가상 포지션 생성
- entry_price, stop_loss, take_profit, timeout_minutes 저장
- 다음 캔들 기준으로 목표/손절/시간청산 판정
- 수수료와 슬리피지를 보수적으로 차감

테스트:
- 익절 케이스
- 손절 케이스
- 시간청산 케이스
- 미체결 케이스
```

## Prompt 7: Streamlit Dashboard

```text
dashboard/streamlit_app.py를 구현하라.
화면:
1. 오늘의 Mr.K 운용 모드 선택
2. 08:50 후보군 테이블
3. 페르소나 점수판
4. 토론 로그
5. 모의 포지션
6. 일간 성과 리포트

실전 주문 버튼은 만들지 말거나 disabled 상태로 두어라.
```

## Prompt 8: 09:00 Runner

```text
app/main.py 또는 app/runner_0900.py에 09:00 전략 runner를 구현하라.

시퀀스:
08:50 후보 스캔
08:55 매기 점수 계산
09:00 Rezo 감시 시작
09:03~09:10 토론/의사결정
09:10~09:30 모의투자 감시
09:40 일간 리포트 생성

실제 시간 실행이 어려우면 replay 모드를 먼저 구현하라.
```

## Prompt 9: 피드백 리포트

```text
feedback/performance.py를 구현하라.
기능:
- 페르소나 점수 bucket별 성과 분석
- Final Score별 성과 분석
- Iris veto 발생 거래 분석
- 실패 원인 태그별 집계
- Markdown 리포트 생성

완료 기준:
- reports/YYYY-MM-DD_daily_report.md 생성
```

---

## 참고자료
- 업비트 거래 데이터 기준 시간: https://support.upbit.com/hc/ko/articles/900006049666-%EA%B1%B0%EB%9E%98-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EA%B8%B0%EC%A4%80-%EC%8B%9C%EA%B0%84%EC%9D%80-%EC%96%B8%EC%A0%9C%EC%9D%B8%EA%B0%80%EC%9A%94
- 업비트 REST API Best Practice: https://docs.upbit.com/kr/docs/rest-api-best-practice
- 업비트 초(Second) 캔들 조회: https://docs.upbit.com/kr/reference/list-candles-seconds
- 업비트 주문 생성 테스트: https://docs.upbit.com/kr/reference/order-test
- 빗썸 Candlestick REST API: https://apidocs.bithumb.com/v1.2.0/reference/candlestick-rest-api
- 빗썸 주문 요청 API: https://apidocs.bithumb.com/v2.1.0/reference/%EC%A3%BC%EB%AC%B8-%EC%9A%94%EC%B2%AD
- 빗썸 Developer Docs: https://apidocs.bithumb.com/docs/%EB%B9%97%EC%8D%B8-developer-docs
