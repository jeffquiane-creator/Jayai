
import streamlit as st
import pandas as pd
import os, json
import io
import streamlit.components.v1 as components

# -------------------- Utilities --------------------
def tts_button(label: str, text: str, key: str):
    """
    Render a browser-based Text-to-Speech play button for the given text.
    Uses the client's SpeechSynthesis API (no server-side deps).
    """
    safe_text = json.dumps(str(text))  # safely serialize for JS
    btn_id = f"tts_{key}"
    html = f"""
    <button id='{btn_id}' style='padding:8px 12px;border-radius:8px;border:1px solid #444;cursor:pointer;'>
      ▶️ {label}
    </button>
    <script>
      const el_{btn_id} = document.getElementById('{btn_id}');
      if (el_{btn_id}) {{
        el_{btn_id}.onclick = () => {{
          const utter = new SpeechSynthesisUtterance({safe_text});
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(utter);
        }};
      }}
    </script>
    """
    components.html(html, height=46)

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()

# -------------------- Data Loading --------------------
DEFAULT_BROKERAGE_FILE = "Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx"
DEFAULT_AGENT_FILE = "Agent_Objections_Rebuttals.xlsx"

BROKERAGE_COLUMNS = ["Brokerage", "Funnel Pilot Rebuttal", "One-Liner", "SMS", "Power Statement"]
AGENT_COLUMNS = ["Objection", "Rebuttal", "One-Liner", "SMS", "AudioPath"]

@st.cache_data
def load_excel_if_exists(path: str, expected_cols: list) -> pd.DataFrame:
    if os.path.exists(path):
        try:
            df = pd.read_excel(path)
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            return df[expected_cols]
        except Exception:
            return pd.DataFrame(columns=expected_cols)
    return pd.DataFrame(columns=expected_cols)

# -------------------- Page Setup --------------------
st.set_page_config(page_title="Funnel Pilot Hub", layout="wide")
st.title("🚀 Funnel Pilot Rebuttal & Brokerage Hub")

# Session state for datasets & favorites
if "brokerage_df" not in st.session_state:
    st.session_state.brokerage_df = load_excel_if_exists(DEFAULT_BROKERAGE_FILE, BROKERAGE_COLUMNS)
if "agent_df" not in st.session_state:
    st.session_state.agent_df = load_excel_if_exists(DEFAULT_AGENT_FILE, AGENT_COLUMNS)
if "favorites" not in st.session_state:
    st.session_state.favorites = []

with st.expander("📦 Data Sources & Upload"):
    colA, colB = st.columns(2)
    with colA:
        st.caption("**Brokerage Comparisons Dataset**")
        st.write("Expected columns:", BROKERAGE_COLUMNS)
        uploaded_broker = st.file_uploader("Upload Brokerage Excel", type=["xlsx"], key="up_broker")
        if uploaded_broker is not None:
            try:
                bdf = pd.read_excel(uploaded_broker)
                for c in BROKERAGE_COLUMNS:
                    if c not in bdf.columns:
                        bdf[c] = ""
                st.session_state.brokerage_df = bdf[BROKERAGE_COLUMNS]
                st.success("Brokerage dataset loaded from upload.")
            except Exception as e:
                st.error(f"Failed to load brokerage file: {e}")
        st.download_button("⬇️ Download Current Brokerage Dataset (Excel)",
                           data=df_to_excel_bytes(st.session_state.brokerage_df),
                           file_name="brokerage_dataset_current.xlsx")
    with colB:
        st.caption("**Agent Objections Dataset**")
        st.write("Expected columns:", AGENT_COLUMNS)
        uploaded_agent = st.file_uploader("Upload Agent Objections Excel", type=["xlsx"], key="up_agent")
        if uploaded_agent is not None:
            try:
                adf = pd.read_excel(uploaded_agent)
                for c in AGENT_COLUMNS:
                    if c not in adf.columns:
                        adf[c] = ""
                st.session_state.agent_df = adf[AGENT_COLUMNS]
                st.success("Agent objections dataset loaded from upload.")
            except Exception as e:
                st.error(f"Failed to load agent objections file: {e}")
        st.download_button("⬇️ Download Current Agent Dataset (Excel)",
                           data=df_to_excel_bytes(st.session_state.agent_df),
                           file_name="agent_objections_current.xlsx")

# -------------------- Top Navigation (Tabs) --------------------
tabs = st.tabs(["🙋 Agent Objections", "🏢 Brokerage Comparison", "⭐ Favorites"])

# -------------------- Agent Objections Tab --------------------
with tabs[0]:
    st.subheader("🙋 Agent Objection Handling")

    adf = st.session_state.agent_df
    if adf.empty:
        st.warning("Agent objection data not found. Upload it above to enable this section.")
    else:
        left, right = st.columns([2, 3])
        with left:
            objection = st.selectbox("Choose an objection:", adf["Objection"].unique())
            row = adf[adf["Objection"] == objection].iloc[0]

        with right:
            st.markdown("#### 🛠️ Full Rebuttal")
            st.text_area("Rebuttal (copy as needed)", value=row["Rebuttal"], height=140, key="agent_reb_txt")
            tts_button("Play Rebuttal", row["Rebuttal"], key="agent_rebuttal")

            st.markdown("#### ⚡ One-Liner")
            st.text_area("One-Liner (copy as needed)", value=row["One-Liner"], height=70, key="agent_ol_txt")
            tts_button("Play One-Liner", row["One-Liner"], key="agent_oneliner")

            st.markdown("#### 📲 SMS Snippet")
            st.text_area("SMS (copy as needed)", value=row["SMS"], height=70, key="agent_sms_txt")
            tts_button("Play SMS", row["SMS"], key="agent_sms")

            if isinstance(row.get("AudioPath"), str) and row.get("AudioPath") and os.path.exists(row["AudioPath"]):
                st.caption("🔊 Uploaded audio file")
                st.audio(row["AudioPath"])

            if st.button("⭐ Add to Favorites", key="fav_add_agent"):
                st.session_state.favorites.append({
                    "type": "objection",
                    "title": row["Objection"],
                    "rebuttal": row["Rebuttal"],
                    "oneliner": row["One-Liner"],
                    "sms": row["SMS"]
                })
                st.success("Added to favorites!")

# -------------------- Brokerage Comparison Tab --------------------
with tabs[1]:
    st.subheader("🏢 Compare Funnel Pilot to Top Brokerages")

    bdf = st.session_state.brokerage_df
    if bdf.empty:
        st.warning("Brokerage dataset not found. Upload it above to enable this section.")
    else:
        left, right = st.columns([2, 3])
        with left:
            brokerage = st.selectbox("Select a brokerage to compare:", bdf["Brokerage"].unique())
            rowb = bdf[bdf["Brokerage"] == brokerage].iloc[0]

        with right:
            st.markdown("#### 🛠️ Full Rebuttal")
            st.text_area("Broker Rebuttal (copy as needed)", value=rowb["Funnel Pilot Rebuttal"], height=140, key="brk_reb_txt")
            tts_button("Play Broker Rebuttal", rowb["Funnel Pilot Rebuttal"], key="broker_rebuttal")

            st.markdown("#### ⚡ One-Liner")
            st.text_area("Broker One-Liner (copy as needed)", value=rowb["One-Liner"], height=70, key="brk_ol_txt")
            tts_button("Play Broker One-Liner", rowb["One-Liner"], key="broker_oneliner")

            st.markdown("#### 📲 SMS Snippet")
            st.text_area("Broker SMS (copy as needed)", value=rowb["SMS"], height=70, key="brk_sms_txt")
            tts_button("Play Broker SMS", rowb["SMS"], key="broker_sms")

            st.markdown("#### 💥 Power Statement")
            st.text_area("Power Statement (copy as needed)", value=rowb["Power Statement"], height=70, key="brk_power_txt")
            tts_button("Play Power Statement", rowb["Power Statement"], key="broker_power")

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("Watch the Demo", "https://honeybadgerpartner.com")
            with col2:
                st.link_button("Book a 3-Way Call", "https://3waycall.com")

            if st.button("⭐ Add to Favorites", key="fav_add_broker"):
                st.session_state.favorites.append({
                    "type": "brokerage",
                    "title": rowb["Brokerage"],
                    "rebuttal": rowb["Funnel Pilot Rebuttal"],
                    "oneliner": rowb["One-Liner"],
                    "sms": rowb["SMS"],
                    "power": rowb["Power Statement"]
                })
                st.success("Added to favorites!")

# -------------------- Favorites Tab --------------------
with tabs[2]:
    st.subheader("⭐ Your Favorites")
    if not st.session_state.favorites:
        st.info("No favorites saved yet. Add some from the other tabs!")
    else:
        for i, fav in enumerate(st.session_state.favorites):
            with st.container():
                st.markdown(f"### {i+1}. {fav['title']} ({fav['type']})")
                st.markdown(f"**Rebuttal:** {fav['rebuttal']}")
                tts_button("Play", fav['rebuttal'], key=f"fav_rebuttal_{i}")
                st.markdown(f"**One-Liner:** {fav['oneliner']}")
                tts_button("Play", fav['oneliner'], key=f"fav_oneliner_{i}")
                st.markdown(f"**SMS:** {fav['sms']}")
                tts_button("Play", fav['sms'], key=f"fav_sms_{i}")
                if fav.get("power"):
                    st.markdown(f"**Power Statement:** {fav['power']}")
                    tts_button("Play", fav['power'], key=f"fav_power_{i}")
                cols = st.columns([1,1,6])
                with cols[0]:
                    if st.button("🗑️ Remove", key=f"fav_remove_{i}"):
                        st.session_state.favorites.pop(i)
                        st.experimental_rerun()
                st.markdown("---")
