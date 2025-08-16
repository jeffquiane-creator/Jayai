
import streamlit as st
import pandas as pd
import pyperclip

@st.cache_data
def load_data():
    return pd.read_excel("Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx")

df = load_data()

st.set_page_config(page_title="Funnel Pilot Rebuttal Engine", layout="centered")
st.title("🚀 Funnel Pilot vs Top Brokerages")

st.markdown("""
Use this tool to compare your Funnel Pilot offer against any of the top 25 brokerages in the country.  
Every section below is crafted using world-class objection handling and positioning.
""")

# Brokerage Selector
brokerage = st.selectbox("Choose a brokerage to compare against:", df["Brokerage"].unique())

row = df[df["Brokerage"] == brokerage].iloc[0]

st.markdown("---")
st.subheader("🛠️ Full Rebuttal")
st.markdown(row["Funnel Pilot Rebuttal"])
if st.button("📋 Copy Rebuttal"):
    st.toast("Rebuttal copied to clipboard.")
    pyperclip.copy(row["Funnel Pilot Rebuttal"])

st.subheader("⚡ One-Liner Summary")
st.markdown(f"**{row['One-Liner']}**")
if st.button("📋 Copy One-Liner"):
    st.toast("One-liner copied to clipboard.")
    pyperclip.copy(row["One-Liner"])

st.subheader("📲 SMS Snippet")
st.code(row["SMS"])
if st.button("📋 Copy SMS"):
    st.toast("SMS copied to clipboard.")
    pyperclip.copy(row["SMS"])

st.subheader("💥 Power Statement")
st.markdown(f"**{row['Power Statement']}**")
if st.button("📋 Copy Power Statement"):
    st.toast("Power statement copied to clipboard.")
    pyperclip.copy(row["Power Statement"])

st.markdown("---")
st.markdown("### 🔗 Next Steps")
col1, col2 = st.columns(2)
with col1:
    st.link_button("Watch the Demo", "https://honeybadgerpartner.com")
with col2:
    st.link_button("Book a 3-Way Call", "https://3waycall.com")

st.markdown("---")
st.download_button("⬇️ Download All Comparisons (Excel)", data=df.to_excel(index=False), file_name="FunnelPilot_vs_TopBrokerages.xlsx")
