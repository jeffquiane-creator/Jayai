
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Funnel Pilot — Agent Objections & Brokerage Comparison")
st.title("🎯 Funnel Pilot — Agent Objections & Brokerage Comparison")

# Sidebar navigation
nav = st.sidebar.radio("Navigate:", ["🤖 Agent Objections", "🏢 Brokerage Comparison", "⭐ Favorites"])

# Load data from upload
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])
df = None
if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)

if df is None:
    st.warning("Please upload a dataset to begin.")
else:
    if nav == "🤖 Agent Objections":
        st.header("Agent Objection Handler")
        objection_list = df['Objection'].dropna().unique()
        selected = st.selectbox("Select an objection", objection_list)
        result = df[df['Objection'] == selected].iloc[0]

        st.subheader("🧠 Rebuttal")
        st.write(result['Rebuttal'])

        st.subheader("💬 SMS Snippet")
        st.code(result.get("SMS", "No SMS provided"), language="text")
        st.button("Copy SMS", key="copy_sms")

        st.subheader("🔊 Listen")
        if "AudioFile" in result and pd.notna(result["AudioFile"]):
            st.audio(result["AudioFile"], format="audio/mp3")
        else:
            st.info("No audio file provided.")

    elif nav == "🏢 Brokerage Comparison":
        st.header("Brokerage Comparison")
        brokerages = df['Brokerage'].dropna().unique()
        selected_brokerage = st.selectbox("Select a brokerage to compare against FunnelPilot", brokerages)
        comp = df[df['Brokerage'] == selected_brokerage].iloc[0]

        st.subheader("📌 Power Statement")
        st.write(comp.get("PowerStatement", "No power statement provided."))

        st.subheader("💬 SMS Snippet")
        st.code(comp.get("SMS", "No SMS provided"), language="text")
        st.button("Copy SMS", key="copy_sms_brokerage")

        st.subheader("🔊 Listen")
        if "AudioFile" in comp and pd.notna(comp["AudioFile"]):
            st.audio(comp["AudioFile"], format="audio/mp3")
        else:
            st.info("No audio file provided.")

    elif nav == "⭐ Favorites":
        st.header("⭐ Favorite Rebuttals")
        st.info("Favorites functionality will be available soon.")
