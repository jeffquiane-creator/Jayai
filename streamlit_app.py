import streamlit as st
import pandas as pd
import os

# --- Page Config ---
st.set_page_config(page_title="Agent Objections & Brokerage Compare", layout="wide")

# --- File paths (adjust if needed) ---
OBJECTIONS_FILE = "Objection_Rebuttal_Master_500 (1).csv"
BROKERAGE_FILE = "Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx"
FUNNELPILOT_FILE = "Top_25_Brokerage_Rebuttals_FunnelPilot.xlsx"

# --- Load Data ---
@st.cache_data
def load_csv(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

@st.cache_data
def load_excel(file):
    return pd.read_excel(file) if os.path.exists(file) else pd.DataFrame()

objections_df = load_csv(OBJECTIONS_FILE)
brokerages_df = load_excel(BROKERAGE_FILE)
funnelpilot_df = load_excel(FUNNELPILOT_FILE)

# --- Initialize Favorites ---
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []

# --- Helper: Copy Button ---
def copy_button(label, text):
    if text and isinstance(text, str):
        st.code(text, language="text")
        st.button(f"📋 Copy {label}", on_click=st.session_state.setdefault, args=("last_copy", text))

# --- Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Agent Objections", "Brokerage Comparison", "My Favorites"])

# --- Agent Objections Page ---
if page == "Agent Objections":
    st.header("Agent Objections")

    if objections_df.empty:
        st.error(f"❌ Could not find {OBJECTIONS_FILE}. Please check that the file exists.")
    else:
        choice = st.selectbox("Select an Objection", objections_df["Objection"].tolist())

        row = objections_df[objections_df["Objection"] == choice].iloc[0]
        st.subheader("Rebuttal")
        st.write(row["Rebuttal"])

        if "PowerStatement" in objections_df.columns:
            st.subheader("Power Statement")
            st.write(row["PowerStatement"])

        if "SMS" in objections_df.columns:
            st.subheader("SMS Snippet")
            copy_button("SMS", row["SMS"])

        if "AudioFile" in objections_df.columns and pd.notna(row["AudioFile"]) and os.path.exists(row["AudioFile"]):
            st.audio(row["AudioFile"])

        if st.button("⭐ Add to Favorites"):
            st.session_state["favorites"].append(("Objection", choice))

# --- Brokerage Comparison Page ---
elif page == "Brokerage Comparison":
    st.header("Brokerage Comparison")

    if brokerages_df.empty or funnelpilot_df.empty:
        st.error("❌ Could not find brokerage datasets. Please check filenames.")
    else:
        brokerages = brokerages_df["Brokerage"].unique().tolist()
        choice = st.selectbox("Select a Brokerage", brokerages)

        rows = brokerages_df[brokerages_df["Brokerage"] == choice]

        st.subheader(f"Comparison: {choice} vs. FunnelPilot")
        for _, row in rows.iterrows():
            st.write(f"**Benefit:** {row['Benefit']}")
            st.write(f"**Power Statement:** {row['PowerStatement']}")
            if "SMS" in row:
                copy_button("SMS", row["SMS"])
            if "AudioFile" in row and pd.notna(row["AudioFile"]) and os.path.exists(row["AudioFile"]):
                st.audio(row["AudioFile"])
            st.markdown("---")

        if st.button("⭐ Add Comparison to Favorites"):
            st.session_state["favorites"].append(("Brokerage", choice))

# --- Favorites Page ---
elif page == "My Favorites":
    st.header("My Favorites")

    if not st.session_state["favorites"]:
        st.info("No favorites saved yet.")
    else:
        for fav_type, fav_item in st.session_state["favorites"]:
            st.write(f"⭐ {fav_type}: {fav_item}")
# Debug: Show what columns exist in the brokerage dataset
st.write("📊 Available columns in brokerage file:", list(brokerage_df.columns))

choice = st.selectbox("Select a Brokerage", brokerage_df["Brokerage"].unique().tolist())

rows = brokerage_df[brokerage_df["Brokerage"] == choice]

st.subheader(f"{choice} vs FunnelPilot")
for _, row in rows.iterrows():
    for col in ["Benefit", "PowerStatement", "SMS", "Rebuttal"]:
        if col in brokerage_df.columns and pd.notna(row[col]):
            st.write(f"**{col}:** {row[col]}")
    if "AudioFile" in brokerage_df.columns and pd.notna(row["AudioFile"]) and os.path.exists(row["AudioFile"]):
        st.audio(row["AudioFile"])
    st.markdown("---")
