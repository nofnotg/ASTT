from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from replay_lab.lake.dataset_registry import DatasetRegistry
from replay_lab.paths import REPLAY_STORE_DIR


st.set_page_config(page_title="ASTT Replay Lab", layout="wide")
st.title("ASTT Replay Lab")

datasets = DatasetRegistry().list_all()
st.subheader("Datasets")
st.dataframe(pd.DataFrame([item.__dict__ for item in datasets]) if datasets else pd.DataFrame())

st.subheader("Experiments")
experiments = sorted((REPLAY_STORE_DIR / "experiments").glob("exp_*"))
rows = []
for exp in experiments:
    metrics_path = exp / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    rows.append({"experiment": exp.name, **metrics})
st.dataframe(pd.DataFrame(rows) if rows else pd.DataFrame())

st.subheader("Approved Exports")
approved = sorted((REPLAY_STORE_DIR / "exports" / "main_app" / "approved_config_patches").glob("*.json"))
st.dataframe(pd.DataFrame({"path": [str(path) for path in approved]}))
