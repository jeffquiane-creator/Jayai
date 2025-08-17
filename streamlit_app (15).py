
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Funnel Pilot — Agent Objections & Brokerage Comparison")
st.title("🎯 Funnel Pilot — Agent Objections & Brokerage Comparison")

# Sidebar navigation
nav = st.sidebar.radio("Navigate:", ["🧠 Agent Objections", "🏢 Brokerage Comparison", "⭐ Favorites"])

# Load data from upload
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])
df = None
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Failed to read file: {e}")

if df is None:
    st.warning("Please upload a dataset to begin.")
else:
    if nav == "🧠 Agent Objections":
        st.subheader("Agent Objection Handling")
        if 'Objection' in df.columns and 'Rebuttal' in df.columns:
            for i, row in df.iterrows():
                with st.expander(row['Objection']):
                    st.markdown(f"**Rebuttal:** {row['Rebuttal']}")
                    if 'SMS' in df.columns:
                        st.code(row['SMS'], language="text")
        else:
            st.error("Missing 'Objection' or 'Rebuttal' columns in the uploaded dataset.")

    elif nav == "🏢 Brokerage Comparison":
        st.subheader("Brokerage Comparison")
        st.dataframe(df)

    elif nav == "⭐ Favorites":
        st.subheader("Your Favorites")
        st.info("Feature coming soon.")
