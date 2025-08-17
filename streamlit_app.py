import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Agent Objections & Brokerage Compare", layout="wide")

# ---- File names (must exist in same folder) ----
OBJECTIONS_FILE = "Objection_Rebuttal_Master_500 (1).csv"
BROKERAGE_FILE = "Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx"

# ---- Load Data ----
def load_csv(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

def load_excel(file):
    return pd.read_excel(file) if os.path.exists(file) else pd.DataFrame()

objections_df = load_csv(OBJECTIONS_FILE)
brokerage_df = load_excel(BROKERAGE_FILE)

# ---- Session State for Favorites ----
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []

# ---- Navigation ----
page = st.sidebar.radio("Go to:", ["Agent Objections", "Brokerage Comparison", "My Favorites"])

# ---- Agent Objections ----
if page == "Agent Objections":
    st.header("Agent Objections")

    if objections_df.empty:
        st.error("❌ Objections dataset not found.")
    else:
        choice = st.selectbox("Select an Objection", objections_df["Objection"].tolist())

        row = objections_df[objections_df["Objection"] == choice].iloc[0]

        st.subheader("Rebuttal")
        st.write(row["Rebuttal"])

        if "SMS" in objections_df.columns:
            st.subheader("SMS")
            st.code(row["SMS"])
            st.button("📋 Copy SMS", on_click=st.session_state.setdefault, args=("last_copy", row["SMS"]))

        if "AudioFile" in objections_df.columns and pd.notna(row["AudioFile"]) and os.path.exists(row["AudioFile"]):
            st.audio(row["AudioFile"])

        if st.button("⭐ Add to Favorites"):
            st.session_state["favorites"].append(("Objection", choice))

# ---- Brokerage Comparison ----
elif page == "Brokerage Comparison":
    st.header("Brokerage Comparison")

    if brokerage_df.empty:
        st.error("❌ Brokerage dataset not found.")
    else:
        choice = st.selectbox("Select a Brokerage", brokerage_df["Brokerage"].unique().tolist())

        rows = brokerage_df[brokerage_df["Brokerage"] == choice]

        st.subheader(f"{choice} vs FunnelPilot")
        for _, row in rows.iterrows():
            st.write(f"**Benefit:** {row['Benefit']}")
            st.write(f"**Power Statement:** {row['PowerStatement']}")
            if "SMS" in row:
                st.code(row["SMS"])
            if "AudioFile" in row and pd.notna(row["AudioFile"]) and os.path.exists(row["AudioFile"]):
                st.audio(row["AudioFile"])
            st.markdown("---")

        if st.button("⭐ Add Comparison to Favorites"):
            st.session_state["favorites"].append(("Brokerage", choice))

# ---- Favorites ----
elif page == "My Favorites":
    st.header("My Favorites")
    if not st.session_state["favorites"]:
        st.info("No favorites saved yet.")
    else:
        for fav_type, fav_item in st.session_state["favorites"]:
            st.write(f"⭐ {fav_type}: {fav_item}")
