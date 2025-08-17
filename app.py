
import streamlit as st
import pandas as pd
import pyttsx3
import tempfile
import os

st.set_page_config(page_title="Agent Objections & Brokerage Compare", layout="wide")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# Session state for favorites
if "favorites" not in st.session_state:
    st.session_state.favorites = []

# Tabs for navigation
tabs = st.tabs(["Agent Objections", "Brokerage Compare", "Power Statements", "My Favorites"])

# ---- Agent Objections Tab ----
with tabs[0]:
    st.header("Agent Objections")
    for _, row in df.iterrows():
        with st.expander(row["Objection"]):
            st.write(row["Rebuttal"])
            if "SMS" in row and not pd.isna(row["SMS"]):
                st.text_area("SMS Snippet", row["SMS"], height=50)
                st.button("Copy SMS", key=f"copy_sms_{_}")
            # Play audio
            if st.button("Play Audio", key=f"audio_{_}"):
                engine = pyttsx3.init()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    engine.save_to_file(row["Rebuttal"], fp.name)
                    engine.runAndWait()
                    st.audio(fp.name)
            # Add to favorites
            if st.button("Add to Favorites", key=f"fav_{_}"):
                st.session_state.favorites.append(dict(row))
                st.success("Added to favorites!")

# ---- Brokerage Compare Tab ----
with tabs[1]:
    st.header("Brokerage Comparison")
    brokerages = df["Brokerage"].dropna().unique()
    choice = st.radio("Select a brokerage:", brokerages)
    subdf = df[df["Brokerage"] == choice]
    for _, row in subdf.iterrows():
        with st.expander(row["Objection"]):
            st.write(row["Rebuttal"])

# ---- Power Statements Tab ----
with tabs[2]:
    st.header("Power Statements")
    power_df = df.dropna(subset=["PowerStatement"])
    for _, row in power_df.iterrows():
        st.info(row["PowerStatement"])

# ---- Favorites Tab ----
with tabs[3]:
    st.header("My Favorites")
    if len(st.session_state.favorites) == 0:
        st.write("No favorites yet.")
    else:
        for fav in st.session_state.favorites:
            with st.expander(fav["Objection"]):
                st.write(fav["Rebuttal"])
                if "SMS" in fav and not pd.isna(fav["SMS"]):
                    st.text_area("SMS Snippet", fav["SMS"], height=50)
