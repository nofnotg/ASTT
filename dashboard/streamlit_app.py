from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from sqlalchemy import select

from app.config import get_settings
from data.schemas import DailyReport, OrderIntentRow, OrderTestResult, PaperPosition, PersonaScore, Signal
from data.storage import Storage
from replay_lab.feedback.report_catalog import ReplayReportCatalog
from replay_lab.paths import REPLAY_STORE_DIR


settings = get_settings()
storage = Storage(settings)

st.set_page_config(page_title="ASTT", layout="wide")
st.title("ASTT Upbit Paper Trading")
st.warning(f"Current mode: {settings.trading_mode.value} | LIVE_TRADING_ENABLED: {settings.live_trading_enabled}")
if settings.trading_mode.value != "LIVE":
    st.info("Actual Upbit orders are blocked.")

category = st.sidebar.radio("Category", ["Live Monitor", "Replay Reports"], index=0)

with storage.session() as session:
    signals = session.execute(select(Signal).order_by(Signal.id.desc()).limit(20)).scalars().all()
    personas = session.execute(select(PersonaScore).order_by(PersonaScore.id.desc()).limit(50)).scalars().all()
    intents = session.execute(select(OrderIntentRow).order_by(OrderIntentRow.id.desc()).limit(20)).scalars().all()
    order_tests = session.execute(select(OrderTestResult).order_by(OrderTestResult.id.desc()).limit(20)).scalars().all()
    positions = session.execute(select(PaperPosition).order_by(PaperPosition.id.desc()).limit(20)).scalars().all()
    reports = session.execute(select(DailyReport).order_by(DailyReport.id.desc()).limit(10)).scalars().all()

if category == "Live Monitor":
    st.subheader("Final Decisions")
    st.dataframe(pd.DataFrame([{"id": s.id, "market": s.market, "score": s.final_score, "decision": s.final_decision, "vetoed": s.vetoed, "veto_reason": s.veto_reason} for s in signals]), use_container_width=True)

    st.subheader("Persona Scores")
    st.dataframe(pd.DataFrame([{"market": p.market, "persona": p.persona_name, "score": p.score, "decision": p.decision, "veto": p.veto, "reasons": json.loads(p.reasons_json)[0] if p.reasons_json else ""} for p in personas]), use_container_width=True)

    st.subheader("Order Intents")
    st.dataframe(pd.DataFrame([{"id": o.id, "market": o.market, "side": o.side, "ord_type": o.ord_type, "krw_amount": o.krw_amount, "status": o.status, "identifier": o.identifier} for o in intents]), use_container_width=True)

    st.subheader("Order Test Results")
    st.dataframe(pd.DataFrame([{"id": o.id, "market": o.market, "status": o.status, "error": o.error_json} for o in order_tests]), use_container_width=True)

    st.subheader("Paper Positions")
    st.dataframe(pd.DataFrame([{"id": p.id, "market": p.market, "avg_price": p.avg_price, "volume": p.volume, "invested_krw": p.invested_krw, "status": p.status, "unrealized_pnl_pct": p.unrealized_pnl_pct} for p in positions]), use_container_width=True)

    st.subheader("Daily Reports")
    st.dataframe(pd.DataFrame([{"date": r.report_date, "signals": r.signal_count, "entered": r.entered_count, "pnl": r.realized_pnl_krw, "path": r.markdown_path} for r in reports]), use_container_width=True)

else:
    if st.button("Refresh replay report catalog"):
        catalog = ReplayReportCatalog().build()
    else:
        catalog = ReplayReportCatalog().load_or_build()
    st.caption("Replay reports are research outputs only. Approved config artifacts must still be imported separately.")
    insights_tab, persona_tab, macro_tab, no_entry_tab, daily_tab, weekly_tab, monthly_tab, windows_tab, files_tab = st.tabs(["Insights", "Personas", "Macro", "No Entry", "Daily", "Weekly", "Monthly", "Time Windows", "Files"])
    with insights_tab:
        st.subheader("Replay Lab Insights")
        insights = catalog.get("insights", {})
        summary = insights.get("summary", {})
        if summary:
            st.dataframe(pd.DataFrame([summary]), use_container_width=True)
        for title, key in [
            ("앱의 가능성", "potential"),
            ("현재 한계", "limits"),
            ("디벨롭한 내용", "developments"),
            ("추가 개선 인사이트", "improvement_insights"),
            ("거시경제/국내정세 인사이트", "macro_context"),
        ]:
            st.markdown(f"### {title}")
            for item in insights.get(key, []):
                st.markdown(f"- {item}")
    with persona_tab:
        st.subheader("Persona Validity")
        st.dataframe(pd.DataFrame(catalog.get("persona_validity", [])), use_container_width=True)
    with macro_tab:
        st.subheader("Macro/Domestic Context Review")
        st.dataframe(pd.DataFrame(catalog.get("macro_persona_context", [])), use_container_width=True)
    with no_entry_tab:
        st.subheader("No Entry Reasons")
        st.dataframe(pd.DataFrame(catalog.get("no_entry_summary", [])), use_container_width=True)
    with daily_tab:
        st.subheader("Replay Daily Reports")
        st.dataframe(pd.DataFrame(catalog["daily"]), use_container_width=True)
    with weekly_tab:
        st.subheader("Replay Weekly Statistics")
        st.dataframe(pd.DataFrame(catalog["weekly"]), use_container_width=True)
    with monthly_tab:
        st.subheader("Replay Monthly Statistics")
        st.dataframe(pd.DataFrame(catalog["monthly"]), use_container_width=True)
    with windows_tab:
        st.subheader("Replay Time Window Statistics")
        st.dataframe(pd.DataFrame(catalog.get("time_windows", [])), use_container_width=True)
    with files_tab:
        report_dir = REPLAY_STORE_DIR / "reports" / "catalog"
        files = sorted([*report_dir.glob("*.md"), *report_dir.glob("*.html")]) if report_dir.exists() else []
        st.dataframe(pd.DataFrame({"path": [str(path) for path in files]}), use_container_width=True)
        selected = st.selectbox("Open replay report", [path.name for path in files]) if files else None
        if selected:
            content = (report_dir / selected).read_text(encoding="utf-8")
            st.code(content, language="html" if selected.endswith(".html") else "markdown")
