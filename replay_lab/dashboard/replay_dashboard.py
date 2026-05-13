from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from replay_lab.feedback.report_catalog import ReplayReportCatalog
from replay_lab.lake.dataset_registry import DatasetRegistry
from replay_lab.paths import REPLAY_STORE_DIR


st.set_page_config(page_title="ASTT Replay Lab", layout="wide")
st.title("ASTT Replay Lab")
section = st.sidebar.radio("Category", ["Overview", "Replay Reports", "Approved Exports"], index=0)

if section == "Overview":
    datasets = DatasetRegistry().list_all()
    st.subheader("Datasets")
    st.dataframe(pd.DataFrame([item.__dict__ for item in datasets]) if datasets else pd.DataFrame(), use_container_width=True)

    st.subheader("Experiments")
    experiments = sorted((REPLAY_STORE_DIR / "experiments").glob("exp_*"))
    rows = []
    for exp in experiments:
        metrics_path = exp / "metrics.json"
        metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
        rows.append({"experiment": exp.name, **metrics})
    st.dataframe(pd.DataFrame(rows) if rows else pd.DataFrame(), use_container_width=True)

elif section == "Replay Reports":
    if st.button("Refresh replay report catalog"):
        catalog = ReplayReportCatalog().build()
    else:
        catalog = ReplayReportCatalog().load_or_build()
    st.caption("Research reports are read-only sidecar outputs. They do not change live settings.")
    insights_tab, daily_tab, weekly_tab, monthly_tab, files_tab = st.tabs(["Insights", "Daily", "Weekly", "Monthly", "Report Files"])
    with insights_tab:
        st.subheader("Replay Lab Insights")
        insights = catalog.get("insights", {})
        summary = insights.get("summary", {})
        if summary:
            st.dataframe(pd.DataFrame([summary]), use_container_width=True)
        for title, key in [
            ("앱의 가능성", "potential"),
            ("현재 한계", "limits"),
            ("디벨롭된 내용", "developments"),
            ("추가 개선 인사이트", "improvement_insights"),
        ]:
            st.markdown(f"### {title}")
            for item in insights.get(key, []):
                st.markdown(f"- {item}")
    with daily_tab:
        st.subheader("Daily Replay Report")
        st.dataframe(pd.DataFrame(catalog["daily"]), use_container_width=True)
    with weekly_tab:
        st.subheader("Weekly Replay Statistics")
        st.dataframe(pd.DataFrame(catalog["weekly"]), use_container_width=True)
    with monthly_tab:
        st.subheader("Monthly Replay Statistics")
        st.dataframe(pd.DataFrame(catalog["monthly"]), use_container_width=True)
    with files_tab:
        st.subheader("Generated Report Files")
        report_dir = REPLAY_STORE_DIR / "reports" / "catalog"
        files = sorted([*report_dir.glob("*.md"), *report_dir.glob("*.html")]) if report_dir.exists() else []
        st.dataframe(pd.DataFrame({"path": [str(path) for path in files]}), use_container_width=True)
        selected = st.selectbox("Open report", [path.name for path in files]) if files else None
        if selected:
            content = (report_dir / selected).read_text(encoding="utf-8")
            st.code(content, language="html" if selected.endswith(".html") else "markdown")

else:
    st.subheader("Approved Exports")
    approved = sorted((REPLAY_STORE_DIR / "exports" / "main_app" / "approved_config_patches").glob("*.json"))
    research = sorted((REPLAY_STORE_DIR / "exports" / "main_app" / "research_summary").glob("*.json"))
    st.dataframe(pd.DataFrame({"path": [str(path) for path in approved + research]}), use_container_width=True)
