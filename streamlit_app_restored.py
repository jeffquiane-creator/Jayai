
import streamlit as st
import pandas as pd
import pyttsx3
import tempfile
import os

st.set_page_config(layout="wide", page_title="Funnel Pilot — Objections & Brokerage")

st.title("🚀 Funnel Pilot Objection & Brokerage Comparison Hub")

# Load objection data
@st.cache_data
def load_data():
    try:
        df1 = pd.read_csv("Objection_Rebuttal_Master_500 (1).csv")
    except:
        df1 = pd.DataFrame()
    try:
        df2 = pd.read_excel("Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx")
    except:
        df2 = pd.DataFrame()
    return df1, df2

objection_df, brokerage_df = load_data()

menu = st.sidebar.radio("Navigate", ["🙋 Agent Objections", "🏢 Brokerage Comparison", "⭐ Favorites"])

def text_to_audio(text):
    engine = pyttsx3.init()
    fd, path = tempfile.mkstemp(suffix=".mp3")
    engine.save_to_file(text, path)
    engine.runAndWait()
    return path

if menu == "🙋 Agent Objections":
    st.header("🙋 Agent Objection Handling")
    if not objection_df.empty:
        selected = st.selectbox("Choose an objection", objection_df['Objection'].dropna().unique())
        match = objection_df[objection_df['Objection'] == selected].iloc[0]
        st.subheader("🎯 Rebuttal")
        st.write(match['Rebuttal'])
        st.subheader("📲 SMS Snippet")
        st.code(match['SMS'], language='text')
        if st.button("🔊 Play Rebuttal Audio"):
            audio_path = text_to_audio(match['Rebuttal'])
            audio_file = open(audio_path, 'rb')
            st.audio(audio_file.read(), format='audio/mp3')
            os.remove(audio_path)
    else:
        st.warning("No objection data found. Please make sure the objection CSV file is in the folder.")

elif menu == "🏢 Brokerage Comparison":
    st.header("🏢 Brokerage Comparison vs Funnel Pilot")
    if not brokerage_df.empty:
        selected = st.selectbox("Select a Brokerage to Compare", brokerage_df['Brokerage'].dropna().unique())
        row = brokerage_df[brokerage_df['Brokerage'] == selected].iloc[0]
        st.subheader("💬 Power Statement")
        st.write(row['PowerStatement'])
        st.subheader("📲 SMS Snippet")
        st.code(row['SMS'], language='text')
        if st.button("🔊 Play Power Statement Audio"):
            audio_path = text_to_audio(row['PowerStatement'])
            audio_file = open(audio_path, 'rb')
            st.audio(audio_file.read(), format='audio/mp3')
            os.remove(audio_path)
    else:
        st.warning("No brokerage data found. Please make sure the Excel file is in the folder.")

elif menu == "⭐ Favorites":
    st.header("⭐ Saved Favorites")
    st.info("This feature is coming soon!")
