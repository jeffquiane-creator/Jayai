import streamlit as st
import pandas as pd
import os

# --- Page Config ---
st.set_page_config(page_title="Agent Objections & Brokerage Compare", layout="wide")

# --- Load Data ---
@st.cache_data
def load_data(file_path):
    if file_path.endswith(".csv"):
        return pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        return pd.read_excel(file_path)
    return pd.DataFrame()

objections_file = "agent_objections.xlsx"   # must have: Objection, Rebuttal, PowerStatement, SMS, AudioFile
brokerages_file = "brokerage_comparison.xlsx"  # must have: Brokerage, Benefit, PowerStatement, SMS, AudioFile

objections_df = load_data(objections_file)
brokerages_df = load_data(brokerages_file)

# --- Initialize Favorites ---
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []

# --- Helper: Copy Button ---
def copy_button(label, text):
    st.code(text, language="text")
    st.button(f"📋 Copy {label}", on_click=st.session_state.setdefault, args=("last_copy", text))

# --- Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Agent Objections", "Brokerage Comparison", "My Favorites"])

# --- Agent Objections Page ---
if page == "Agent Objections":
    st.header("Agent Objections")

    if objections_df.empty:
        st.warning("⚠️ No objection data file found.")
    else:
        choice = st.selectbox("Select an Objection", objections_df["Objection"].tolist())

        row = objections_df[objections_df["Objection"] == choice].iloc[0]
        st.subheader("Rebuttal")
        st.write(row["Rebuttal"])

        st.subheader("Power Statement")
        st.write(row["PowerStatement"])

        st.subheader("SMS Snippet")
        copy_button("SMS", row["SMS"])

        if pd.notna(row.get("AudioFile", "")) and os.path.exists(row["AudioFile"]):
            st.audio(row["AudioFile"])

        if st.button("⭐ Add to Favorites"):
            st.session_state["favorites"].append(("Objection", choice))

# --- Brokerage Comparison Page ---
elif page == "Brokerage Comparison":
    st.header("Brokerage Comparison")

    if brokerages_df.empty:
        st.warning("⚠️ No brokerage comparison file found.")
    else:
        brokerages = brokerages_df["Brokerage"].unique().tolist()
        choice = st.selectbox("Select a Brokerage", brokerages)

        rows = brokerages_df[brokerages_df["Brokerage"] == choice]

        st.subheader(f"Comparison: {choice} vs. FunnelPilot")
        for _, row in rows.iterrows():
            st.write(f"**Benefit:** {row['Benefit']}")
            st.write(f"**Power Statement:** {row['PowerStatement']}")
            copy_button("SMS", row["SMS"])
            if pd.notna(row.get("AudioFile", "")) and os.path.exists(row["AudioFile"]):
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

