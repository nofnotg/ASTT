# ASTT Upbit Paper Trading MVP

ASTT is an Upbit-only live paper trading MVP. It uses real Upbit market data, generates persona scores, creates a final decision, records order intents, fills virtual paper positions, and writes daily reports.

This project is not a default live trading bot. Real Upbit orders are hard-blocked unless both conditions are true:

```env
TRADING_MODE=LIVE
LIVE_TRADING_ENABLED=true
```

## Important Key Notice

The API key previously pasted in conversation must be treated as exposed. Revoke it in Upbit and create a new key before using authenticated features.

Use the minimum permissions:

- Public market data and PAPER mode: no API key required.
- Asset/account checks and orders/test: API key required.
- `/v1/orders/test`: requires Upbit order permission, but does not create a real order.
- Withdrawal permission: never use it.

Secrets must be placed only in `.env`. Do not commit `.env`.

## Install

```bash
cd C:\ASTT
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Then edit `.env` manually:

```env
UPBIT_ACCESS_KEY=
UPBIT_SECRET_KEY=
UPBIT_ALLOWED_IP=
```

## Commands

Public API check:

```bash
python -m app.main --check-public
```

Authenticated header check:

```bash
python -m app.main --check-auth
```

Paper mode:

```bash
python -m app.main --mode paper
```

09:00 replay:

```bash
python -m app.runner_0900 --replay
```

Order test mode:

```bash
python -m app.runner_0900 --mode order_test --replay
```

Dashboard:

```bash
streamlit run dashboard/streamlit_app.py
```

Tests:

```bash
pytest
pytest -m integration
```

## Safety Guards

- Default mode is `PAPER`.
- Default `LIVE_TRADING_ENABLED` is `false`.
- `LiveBroker` raises unless `TRADING_MODE=LIVE` and `LIVE_TRADING_ENABLED=true`.
- Iris veto blocks order intent creation/submission.
- CostA DCA is disabled by default.
- `orders/test` results are stored separately and their UUIDs are not used for real order lookup or cancel flows.

## MVP Flow

```text
Upbit real data
-> 09:00 candidate scan
-> Mr.K / Maggie / Rezo / CostA / Iris
-> Iris veto
-> FinalDecision
-> OrderIntent
-> PaperBroker or OrderTestBroker
-> Daily report
-> Feedback loop
```

Performance must be read as total virtual assets:

```text
total assets = virtual cash + marked paper positions
```

## Replay Lab Sidecar

Replay Lab is a sidecar research environment. It does not run in the live app path and it never calls real order APIs, `orders/test`, or LIVE mode. It uses public historical data, local cache, replay clocks, PAPER replay fills, markdown reports, and APPROVED-only export artifacts.

Core boundary:

```text
Main App = live operation engine
Replay Lab = historical research and validation lab
```

Replay Lab connects back to the main app only through approved artifacts:

```text
replay_store/exports/main_app/
feedback/import_replay_artifacts.py --preview
```

### Replay Commands

Load historical candles:

```bash
python -m replay_lab.app.replay_cli load-candles --market KRW-BTC --timeframe 1m --days 90
```

Load 09:00 windows:

```bash
python -m replay_lab.app.replay_cli load-0900 --days 30 --top-markets 50 --markets KRW-BTC,KRW-ETH
```

Run a single replay:

```bash
python -m replay_lab.app.replay_cli run-0900 --date 2026-02-10 --markets KRW-BTC,KRW-ETH
```

Run a batch replay:

```bash
python -m replay_lab.app.replay_cli batch-0900 --days 30 --top-markets 50 --markets KRW-BTC,KRW-ETH
```

Walk-forward window generation:

```bash
python -m replay_lab.app.replay_cli walk-forward --days 90 --top-markets 50
```

Review an experiment:

```bash
python -m replay_lab.app.replay_cli athena-review --experiment-id exp_YYYYMMDD_HHMMSS
```

Preview approved main-app imports:

```bash
python -m feedback.import_replay_artifacts --preview
```

Dashboard:

```bash
streamlit run replay_lab/dashboard/replay_dashboard.py
```

Safety rules:

- ReplayClock blocks future data access to avoid lookahead bias.
- Replay Lab uses public historical data by default and does not require API keys.
- Replay results do not change main app config automatically.
- Main app import accepts only `APPROVED` artifacts with schema version `1.0`.
