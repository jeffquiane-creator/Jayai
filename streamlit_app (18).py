
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Funnel Pilot — Agent Objections & Brokerage Comparison", layout="wide")

st.title("🎯 Funnel Pilot — Agent Objections & Brokerage Comparison")

nav = st.sidebar.radio("Navigate:", ["🤖 Agent Objections", "🏢 Brokerage Comparison", "⭐ Favorites"])

uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])
df = None

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error loading file: {e}")

if df is not None:
    if nav == "🤖 Agent Objections":
        if "Objection" in df.columns:
            objection = st.selectbox("Choose an objection", df["Objection"].dropna().unique())
            row = df[df["Objection"] == objection].iloc[0]
            st.subheader("💬 Rebuttal")
            st.write(row.get("Rebuttal", "—"))

            if "PowerStatement" in row:
                st.subheader("💥 Power Statement")
                st.write(row["PowerStatement"])

            if "SMS" in row:
                st.text_area("📲 SMS Snippet", row["SMS"])
                st.download_button("Copy SMS", row["SMS"], file_name="sms.txt")

            if "Audio" in row and pd.notna(row["Audio"]):
                st.audio(row["Audio"])

        else:
            st.warning("Expected column 'Objection' not found in uploaded file.")

    elif nav == "🏢 Brokerage Comparison":
        if "Brokerage" in df.columns:
            brokerages = df["Brokerage"].dropna().unique().tolist()
            selected = st.selectbox("Select a brokerage to compare", brokerages)
            row = df[df["Brokerage"] == selected].iloc[0]

            st.subheader(f"🔍 Comparison: {selected} vs FunnelPilot")
            st.write(row.get("Comparison", "—"))

            if "PowerStatement" in row:
                st.subheader("💥 Power Statement")
                st.write(row["PowerStatement"])

            if "SMS" in row:
                st.text_area("📲 SMS Snippet", row["SMS"])
                st.download_button("Copy SMS", row["SMS"], file_name="sms.txt")

            if "Audio" in row and pd.notna(row["Audio"]):
                st.audio(row["Audio"])

        else:
            st.warning("Expected column 'Brokerage' not found in uploaded file.")

    elif nav == "⭐ Favorites":
        st.info("Favorites feature is not implemented in this version.")
else:
    st.warning("Please upload a dataset to begin.")
