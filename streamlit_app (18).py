
import streamlit as st
import pandas as pd

# Load data (assumes file is in same directory or update with correct path)
@st.cache_data
def load_data():
    return pd.read_excel("Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx")

df = load_data()

# App Title
st.title("🏆 Funnel Pilot vs Top 25 Brokerages")

st.write("Compare your current brokerage to our all-in-one, done-for-you system built to help you close faster and scale without effort.")

# Dropdown to select brokerage
brokerage_names = df["Brokerage"].tolist()
selected_brokerage = st.selectbox("Select a brokerage to compare against:", brokerage_names)

# Get selected row
selected_row = df[df["Brokerage"] == selected_brokerage].iloc[0]

# Display rebuttal
st.subheader("🛠️ Full Rebuttal")
st.markdown(f"{selected_row['Funnel Pilot Rebuttal']}")

# One-liner
st.subheader("⚡ One-Liner Summary")
st.markdown(f"**{selected_row['One-Liner']}**")

# SMS
st.subheader("📲 SMS Snippet")
st.code(selected_row['SMS'])

# Power Statement
st.subheader("💥 Power Statement")
st.markdown(f"**{selected_row['Power Statement']}**")

# Optional call-to-action
st.markdown("---")
st.markdown("🔗 Want to see how it works? [Book a Call »](https://3waycall.com) or [Watch the Demo »](https://honeybadgerpartner.com)")
