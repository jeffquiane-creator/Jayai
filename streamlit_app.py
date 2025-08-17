import random
from pathlib import Path
import json
import re
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------- Config ----------------
OBJECTION_FILES = [
    "Objection_Rebuttal_Master_500.csv",
    "Objection_Rebuttal_Master_500 (1).csv",
    "Agent_Objection_Rebuttals_Dataset_Categorized.csv",
]

BROKERAGE_FILE = "Top_25_Brokerage_Rebuttals_Final.csv"

HEADER_ALIASES = {
    "question": ["objection", "question"],
    "answer":   ["rebuttal", "answer"],
    "category": ["category", "topic"],
    "sms":      ["sms"],
    "power":    ["power statement", "power", "benefit"],
}

def _lowerstrip(s): 
    return str(s).strip().lower()

def _find_col(cols, targets):
    cols_l = [_lowerstrip(c) for c in cols]
    for t in targets:
        if t in cols_l:
            return cols[cols_l.index(t)]
    return None

@st.cache_data
def load_csv(candidates):
    base = Path(__file__).parent
    for name in candidates:
        p = base / name
        if p.exists():
            df = pd.read_csv(p).dropna(axis=1, how="all")
            return df, p.name
    raise FileNotFoundError(f"Couldn’t find any of: {candidates}")

def copy_button(label, text, key):
    safe = json.dumps(text)
    html = f"""
    <button id="{key}" style="padding:6px 10px; font-size:12px; margin:4px; cursor:pointer;">
      {label}
    </button>
    <script>
    const btn_{key.replace("-", "_")} = document.getElementById("{key}");
    btn_{key.replace("-", "_")}.onclick = async () => {{
        try {{ await navigator.clipboard.writeText({safe}); }} catch(e){{console.log(e);}}
    }};
    </script>
    """
    components.html(html, height=40)

def tts_button(text, key):
    safe = json.dumps(text)
    html = f"""
    <button id="play_{key}" style="padding:6px 10px; font-size:12px; margin:4px; cursor:pointer;">
      ▶ Play
    </button>
    <script>
    const u = new SpeechSynthesisUtterance({safe});
    document.getElementById("play_{key}").onclick = () => window.speechSynthesis.speak(u);
    </script>
    """
    components.html(html, height=40)

# ---------------- Main ----------------
st.set_page_config(page_title="Funnel Pilot — Agent Objections & Brokerage Comparison", layout="wide")
st.title("🎯 Funnel Pilot — Agent Objections & Brokerage Comparison")

nav = st.sidebar.radio("Navigate:", ["🗣 Agent Objections", "🏢 Brokerage Comparison", "⭐ Favorites"])

if nav == "🗣 Agent Objections":
    df, used = load_csv(OBJECTION_FILES)
    st.caption(f"Using: {used}")

    q_col = _find_col(df.columns, HEADER_ALIASES["question"])
    a_col = _find_col(df.columns, HEADER_ALIASES["answer"])
    s_col = _find_col(df.columns, HEADER_ALIASES["sms"])

    if q_col and a_col:
        options = df[q_col].tolist()
        selected = st.selectbox("Pick an objection", options, index=0)
        row = df[df[q_col] == selected].iloc[0]

        st.subheader("Objection")
        st.write(row[q_col])

        st.subheader("Rebuttal")
        st.write(row[a_col])
        copy_button("Copy Rebuttal", row[a_col], key="rebuttal")
        tts_button(row[a_col], key="rebuttal")

        if s_col and isinstance(row[s_col], str) and row[s_col].strip():
            st.markdown("---")
            st.subheader("SMS Snippet")
            st.code(row[s_col], language="text")
            copy_button("Copy SMS", row[s_col], key="sms")
            st.download_button("Download SMS", row[s_col], file_name="sms.txt")

elif nav == "🏢 Brokerage Comparison":
    df, used = load_csv([BROKERAGE_FILE])
    st.caption(f"Using: {used}")

    b_col = _find_col(df.columns, ["brokerage"])
    p_col = _find_col(df.columns, HEADER_ALIASES["power"])
    s_col = _find_col(df.columns, HEADER_ALIASES["sms"])

    brokerages = df[b_col].unique().tolist()
    selected = st.selectbox("Select a brokerage to compare", brokerages)
    row = df[df[b_col] == selected].iloc[0]

    st.subheader(f"Comparison: {selected} vs FunnelPilot")
    st.write(row[p_col])
    copy_button("Copy Power Statement", row[p_col], key="power")
    tts_button(row[p_col], key="power")

    if s_col and isinstance(row[s_col], str) and row[s_col].strip():
        st.markdown("---")
        st.subheader("SMS Snippet")
        st.code(row[s_col], language="text")
        copy_button("Copy SMS", row[s_col], key="broker-sms")
        st.download_button("Download SMS", row[s_col], file_name="broker_sms.txt")

elif nav == "⭐ Favorites":
    st.info("Favorites functionality can be wired to a persistent store later.")
