
import streamlit as st
import pandas as pd
import os

# Load brokerage data
@st.cache_data
def load_brokerage_data():
    return pd.read_excel("Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx")

# Load agent objection data
@st.cache_data
def load_agent_data():
    if os.path.exists("Agent_Objections_Rebuttals.xlsx"):
        return pd.read_excel("Agent_Objections_Rebuttals.xlsx")
    else:
        return pd.DataFrame(columns=["Objection", "Rebuttal", "One-Liner", "SMS", "AudioPath"])

brokerage_df = load_brokerage_data()
agent_df = load_agent_data()

# Page config
st.set_page_config(page_title="Funnel Pilot Hub", layout="centered")
st.title("🚀 Funnel Pilot Rebuttal & Brokerage Hub")

# Initialize favorites in session state
if "favorites" not in st.session_state:
    st.session_state.favorites = []

# Tabs
tabs = st.tabs(["🙋 Agent Objections", "🏢 Brokerage Comparison", "⭐ Favorites"])

# --- Agent Objections Tab ---
with tabs[0]:
    st.header("🙋 Agent Objection Handling")

    if agent_df.empty:
        st.warning("Agent objection data not found. Please upload 'Agent_Objections_Rebuttals.xlsx'.")
    else:
        objection = st.selectbox("Choose an objection:", agent_df["Objection"].unique())
        row = agent_df[agent_df["Objection"] == objection].iloc[0]

        st.subheader("🛠️ Full Rebuttal")
        st.text_area("Rebuttal", value=row["Rebuttal"], height=100)

        st.subheader("⚡ One-Liner")
        st.text_area("One-Liner", value=row["One-Liner"], height=60)

        st.subheader("📲 SMS Snippet")
        st.text_area("SMS", value=row["SMS"], height=60)

        st.subheader("🔊 Audio (if available)")
        if row.get("AudioPath") and os.path.exists(str(row["AudioPath"])):
            st.audio(row["AudioPath"])
        else:
            st.info("No audio file found for this rebuttal.")

        if st.button("⭐ Add to Favorites (Objection)"):
            st.session_state.favorites.append({
                "type": "objection",
                "title": row["Objection"],
                "rebuttal": row["Rebuttal"],
                "oneliner": row["One-Liner"],
                "sms": row["SMS"]
            })
            st.success("Added to favorites!")

# --- Brokerage Comparison Tab ---
with tabs[1]:
    st.header("🏢 Brokerage Comparison")

    brokerage = st.selectbox("Select a brokerage to compare:", brokerage_df["Brokerage"].unique())
    row = brokerage_df[brokerage_df["Brokerage"] == brokerage].iloc[0]

    st.subheader("🛠️ Full Rebuttal")
    st.text_area("Broker Rebuttal", value=row["Funnel Pilot Rebuttal"], height=100)

    st.subheader("⚡ One-Liner")
    st.text_area("Broker One-Liner", value=row["One-Liner"], height=60)

    st.subheader("📲 SMS Snippet")
    st.text_area("Broker SMS", value=row["SMS"], height=60)

    st.subheader("💥 Power Statement")
    st.text_area("Power Statement", value=row["Power Statement"], height=60)

    st.markdown("### 🔗 Next Steps")
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("Watch the Demo", "https://honeybadgerpartner.com")
    with col2:
        st.link_button("Book a 3-Way Call", "https://3waycall.com")

    if st.button("⭐ Add to Favorites (Brokerage)"):
        st.session_state.favorites.append({
            "type": "brokerage",
            "title": row["Brokerage"],
            "rebuttal": row["Funnel Pilot Rebuttal"],
            "oneliner": row["One-Liner"],
            "sms": row["SMS"],
            "power": row["Power Statement"]
        })
        st.success("Added to favorites!")

# --- Favorites Tab ---
with tabs[2]:
    st.header("⭐ Your Favorites")
    if not st.session_state.favorites:
        st.info("No favorites saved yet. Add some from the other tabs!")
    else:
        for i, fav in enumerate(st.session_state.favorites):
            st.markdown(f"### {i+1}. {fav['title']} ({fav['type']})")
            st.markdown(f"**Rebuttal:** {fav['rebuttal']}")
            st.markdown(f"**One-Liner:** {fav['oneliner']}")
            st.markdown(f"**SMS:** {fav['sms']}")
            if fav["type"] == "brokerage":
                st.markdown(f"**Power Statement:** {fav['power']}")
            st.markdown("---")
