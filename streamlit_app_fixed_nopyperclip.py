
import streamlit as st
import pandas as pd
import os

@st.cache_data
def load_brokerage_data():
    return pd.read_excel("Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx")

@st.cache_data
def load_agent_data():
    if os.path.exists("Agent_Objections_Rebuttals.xlsx"):
        return pd.read_excel("Agent_Objections_Rebuttals.xlsx")
    else:
        return pd.DataFrame(columns=["Objection", "Rebuttal", "One-Liner", "SMS", "AudioPath"])

brokerage_df = load_brokerage_data()
agent_df = load_agent_data()

st.set_page_config(page_title="Funnel Pilot Objection & Rebuttal Engine", layout="centered")
st.title("🎯 Funnel Pilot Rebuttal & Brokerage Comparison Tool")

# Sidebar navigation
nav = st.sidebar.radio("Navigate", ["Agent Objections", "Brokerage Comparisons"])

# --- AGENT OBJECTION HANDLER ---
if nav == "Agent Objections":
    st.header("🙋 Agent Objection Handling")

    if agent_df.empty:
        st.warning("Agent objection data not found. Please upload 'Agent_Objections_Rebuttals.xlsx'.")
    else:
        objection = st.selectbox("Select an objection to view rebuttals:", agent_df["Objection"].unique())
        row = agent_df[agent_df["Objection"] == objection].iloc[0]

        st.subheader("🛠️ Full Rebuttal")
        st.text_area("Copy Rebuttal", value=row["Rebuttal"], height=100)

        st.subheader("⚡ One-Liner")
        st.text_area("Copy One-Liner", value=row["One-Liner"], height=60)

        st.subheader("📲 SMS")
        st.text_area("Copy SMS", value=row["SMS"], height=60)

        if row.get("AudioPath") and os.path.exists(row["AudioPath"]):
            st.subheader("🔊 Listen to Rebuttal")
            st.audio(row["AudioPath"])
        else:
            st.subheader("🔊 Listen to Rebuttal")
            st.info("No audio available for this rebuttal.")

# --- BROKERAGE COMPARISON TOOL ---
if nav == "Brokerage Comparisons":
    st.header("🏢 Compare Funnel Pilot to Other Brokerages")

    brokerage = st.selectbox("Choose a brokerage to compare:", brokerage_df["Brokerage"].unique())
    row = brokerage_df[brokerage_df["Brokerage"] == brokerage].iloc[0]

    st.subheader("🛠️ Full Rebuttal")
    st.text_area("Copy Rebuttal", value=row["Funnel Pilot Rebuttal"], height=100)

    st.subheader("⚡ One-Liner")
    st.text_area("Copy One-Liner", value=row["One-Liner"], height=60)

    st.subheader("📲 SMS")
    st.text_area("Copy SMS", value=row["SMS"], height=60)

    st.subheader("💥 Power Statement")
    st.text_area("Copy Power Statement", value=row["Power Statement"], height=60)

    st.markdown("---")
    st.markdown("### 🔗 Next Steps")
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("Watch the Demo", "https://honeybadgerpartner.com")
    with col2:
        st.link_button("Book a 3-Way Call", "https://3waycall.com")

    st.download_button("⬇️ Download Broker Comparison (Excel)", data=brokerage_df.to_excel(index=False), file_name="FunnelPilot_vs_TopBrokerages.xlsx")
