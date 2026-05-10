from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from sqlalchemy import select

from app.config import get_settings
from data.schemas import DailyReport, OrderIntentRow, OrderTestResult, PaperPosition, PersonaScore, Signal
from data.storage import Storage


settings = get_settings()
storage = Storage(settings)

st.set_page_config(page_title="ASTT", layout="wide")
st.title("ASTT Upbit Paper Trading")
st.warning(f"Current mode: {settings.trading_mode.value} | LIVE_TRADING_ENABLED: {settings.live_trading_enabled}")
if settings.trading_mode.value != "LIVE":
    st.info("Actual Upbit orders are blocked.")

with storage.session() as session:
    signals = session.execute(select(Signal).order_by(Signal.id.desc()).limit(20)).scalars().all()
    personas = session.execute(select(PersonaScore).order_by(PersonaScore.id.desc()).limit(50)).scalars().all()
    intents = session.execute(select(OrderIntentRow).order_by(OrderIntentRow.id.desc()).limit(20)).scalars().all()
    order_tests = session.execute(select(OrderTestResult).order_by(OrderTestResult.id.desc()).limit(20)).scalars().all()
    positions = session.execute(select(PaperPosition).order_by(PaperPosition.id.desc()).limit(20)).scalars().all()
    reports = session.execute(select(DailyReport).order_by(DailyReport.id.desc()).limit(10)).scalars().all()

st.subheader("Final Decisions")
st.dataframe(pd.DataFrame([{"id": s.id, "market": s.market, "score": s.final_score, "decision": s.final_decision, "vetoed": s.vetoed, "veto_reason": s.veto_reason} for s in signals]))

st.subheader("Persona Scores")
st.dataframe(pd.DataFrame([{"market": p.market, "persona": p.persona_name, "score": p.score, "decision": p.decision, "veto": p.veto, "reasons": json.loads(p.reasons_json)[0] if p.reasons_json else ""} for p in personas]))

st.subheader("Order Intents")
st.dataframe(pd.DataFrame([{"id": o.id, "market": o.market, "side": o.side, "ord_type": o.ord_type, "krw_amount": o.krw_amount, "status": o.status, "identifier": o.identifier} for o in intents]))

st.subheader("Order Test Results")
st.dataframe(pd.DataFrame([{"id": o.id, "market": o.market, "status": o.status, "error": o.error_json} for o in order_tests]))

st.subheader("Paper Positions")
st.dataframe(pd.DataFrame([{"id": p.id, "market": p.market, "avg_price": p.avg_price, "volume": p.volume, "invested_krw": p.invested_krw, "status": p.status, "unrealized_pnl_pct": p.unrealized_pnl_pct} for p in positions]))

st.subheader("Daily Reports")
st.dataframe(pd.DataFrame([{"date": r.report_date, "signals": r.signal_count, "entered": r.entered_count, "pnl": r.realized_pnl_krw, "path": r.markdown_path} for r in reports]))

