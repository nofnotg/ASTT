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

