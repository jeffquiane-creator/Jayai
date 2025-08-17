
import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide", page_title="Funnel Pilot — Agent Objections & Brokerage Comparison")
st.title("🎯 Funnel Pilot — Agent Objections & Brokerage Comparison")

# Sidebar navigation
nav = st.sidebar.radio("Navigate:", ["🧠 Agent Objections", "🏢 Brokerage Comparison", "⭐ Favorites"])

# Load data from file or upload
default_path = "Objection_Rebuttal_Master_500 (1).csv"
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    st.success(f"Uploaded file: {uploaded_file.name}")
elif os.path.exists(default_path):
    df = pd.read_csv(default_path)
    st.success(f"Auto-loaded dataset: {default_path}")
else:
    df = None
    st.warning("Please upload a dataset to begin.")

if df is not None:
    if nav == "🧠 Agent Objections":
        st.subheader("Agent Objection Handling")
        st.dataframe(df)
    elif nav == "🏢 Brokerage Comparison":
        st.subheader("Brokerage Comparison")
        st.dataframe(df)
    elif nav == "⭐ Favorites":
        st.subheader("Your Favorites (coming soon...)")
