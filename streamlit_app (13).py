
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Funnel Pilot — Agent Objections & Brokerage Comparison")
st.title("🎯 Funnel Pilot — Agent Objections & Brokerage Comparison")

# Sidebar navigation
nav = st.sidebar.radio("Navigate:", ["🙋‍♂️ Agent Objections", "🏢 Brokerage Comparison", "⭐ Favorites"])

# Load data from upload
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])
df = None
if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

if df is not None:
    if nav == "🙋‍♂️ Agent Objections":
        st.subheader("Agent Objection Handling")
        for idx, row in df.iterrows():
            st.markdown(f"**❓ Objection:** {row.get('Objection', '')}")
            st.markdown(f"💬 **Rebuttal:** {row.get('Rebuttal', '')}")
            st.markdown(f"💥 **Power Statement:** {row.get('PowerStatement', '')}")
            if 'SMS' in row:
                st.code(row['SMS'], language='text')
            if 'AudioFile' in row and pd.notna(row['AudioFile']):
                st.audio(row['AudioFile'], format='audio/mp3')

    elif nav == "🏢 Brokerage Comparison":
        st.subheader("Brokerage Comparison")
        st.dataframe(df)

    elif nav == "⭐ Favorites":
        st.subheader("Favorites (placeholder)")
        st.info("This section will let you save and view your favorite rebuttals.")
else:
    st.warning("Please upload a dataset to begin.")
