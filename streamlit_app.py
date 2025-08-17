
import streamlit as st
import pandas as pd
import os, json, io
import streamlit.components.v1 as components

# -------------------- Utility UI elements --------------------
def tts_button(label, text, key):
    """Browser Text-to-Speech play button (no server deps)."""
    safe_text = json.dumps(str(text))  # safe for JS
    btn_id = f"tts_{key}"
    html = f"""
    <button id='{btn_id}' style='padding:8px 12px;border-radius:8px;border:1px solid #444;cursor:pointer;margin:6px 6px 0 0'>
      ▶️ {label}
    </button>
    <script>
      const el_{btn_id} = document.getElementById('{btn_id}');
      if (el_{btn_id}) {{
        el_{btn_id}.onclick = () => {{
          try {{
            const utter = new SpeechSynthesisUtterance({safe_text});
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utter);
          }} catch(e) {{
            alert("Text-to-speech not available in this browser.");
          }}
        }};
      }}
    </script>
    """
    components.html(html, height=48)

def copy_button(label, text, key):
    """JS clipboard copy button (works on https)."""
    safe_text = json.dumps(str(text))
    btn_id = f"copy_{key}"
    html = f"""
    <button id='{btn_id}' style='padding:8px 10px;border-radius:8px;border:1px solid #444;cursor:pointer;margin:6px 0 0 6px'>
      📋 Copy {label}
    </button>
    <script>
      const btn_{btn_id} = document.getElementById('{btn_id}');
      if (btn_{btn_id} && navigator.clipboard) {{
        btn_{btn_id}.onclick = async () => {{
          try {{
            await navigator.clipboard.writeText({safe_text});
          }} catch (e) {{
            alert('Copy blocked by browser; select and copy manually.');
          }}
        }};
      }}
    </script>
    """
    components.html(html, height=42)

def df_to_excel_bytes(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()

# -------------------- Data loading helpers --------------------
BROKERAGE_FILE = "Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx"
AGENT_FILE = "Agent_Objections_Rebuttals.xlsx"

BROKERAGE_COLS = ["Brokerage", "Funnel Pilot Rebuttal", "One-Liner", "SMS", "Power Statement"]
AGENT_COLS = ["Objection", "Rebuttal", "One-Liner", "SMS", "AudioPath"]

@st.cache_data
def load_excel_if_exists(path, expected_cols):
    if os.path.exists(path):
        try:
            df = pd.read_excel(path)
            for c in expected_cols:
                if c not in df.columns:
                    df[c] = ""
            return df[expected_cols]
        except Exception:
            return pd.DataFrame(columns=expected_cols)
    return pd.DataFrame(columns=expected_cols)

# -------------------- Page setup --------------------
st.set_page_config(page_title="Funnel Pilot Hub", layout="wide")
st.title("🚀 Funnel Pilot Rebuttal & Brokerage Hub")

# session state
if "brokerage_df" not in st.session_state:
    st.session_state.brokerage_df = load_excel_if_exists(BROKERAGE_FILE, BROKERAGE_COLS)
if "agent_df" not in st.session_state:
    st.session_state.agent_df = load_excel_if_exists(AGENT_FILE, AGENT_COLS)
if "favorites" not in st.session_state:
    st.session_state.favorites = []

# -------------------- Data controls --------------------
with st.expander("📦 Data Sources & Upload"):
    c1, c2 = st.columns(2)
    with c1:
        st.caption("**Brokerage Comparisons Dataset**")
        st.write("Expected columns:", BROKERAGE_COLS)
        up_b = st.file_uploader("Upload Brokerage Excel (xlsx) or CSV", type=["xlsx", "csv"], key="up_broker")
        if up_b is not None:
            try:
                if up_b.name.lower().endswith(".csv"):
                    bdf = pd.read_csv(up_b)
                else:
                    bdf = pd.read_excel(up_b)
                for c in BROKERAGE_COLS:
                    if c not in bdf.columns:
                        bdf[c] = ""
                st.session_state.brokerage_df = bdf[BROKERAGE_COLS]
                st.success("Brokerage dataset loaded.")
            except Exception as e:
                st.error(f"Failed to load brokerage file: {e}")
        st.download_button(
            "⬇️ Download Current Brokerage Dataset (Excel)",
            data=df_to_excel_bytes(st.session_state.brokerage_df),
            file_name="brokerage_dataset_current.xlsx",
        )
    with c2:
        st.caption("**Agent Objections Dataset**")
        st.write("Expected columns:", AGENT_COLS)
        up_a = st.file_uploader("Upload Agent Objections Excel (xlsx) or CSV", type=["xlsx", "csv"], key="up_agent")
        if up_a is not None:
            try:
                if up_a.name.lower().endswith(".csv"):
                    adf = pd.read_csv(up_a)
                else:
                    adf = pd.read_excel(up_a)
                for c in AGENT_COLS:
                    if c not in adf.columns:
                        adf[c] = ""
                st.session_state.agent_df = adf[AGENT_COLS]
                st.success("Agent objections dataset loaded.")
            except Exception as e:
                st.error(f"Failed to load agent objections file: {e}")
        st.download_button(
            "⬇️ Download Current Agent Dataset (Excel)",
            data=df_to_excel_bytes(st.session_state.agent_df),
            file_name="agent_objections_current.xlsx",
        )

# -------------------- Tabs --------------------
tab_objs, tab_brok, tab_favs = st.tabs(["🙋 Agent Objections", "🏢 Brokerage Comparison", "⭐ Favorites"])

# ========== Agent Objections ==========
with tab_objs:
    st.subheader("🙋 Agent Objection Handling")
    adf = st.session_state.agent_df
    if adf.empty:
        st.warning("No agent objection data found. Place Agent_Objections_Rebuttals.xlsx next to this app or upload above.")
    else:
        left, right = st.columns([2, 3])
        with left:
            # search
            q = st.text_input("Search objections / one-liners / SMS", "")
            if q.strip():
                mask = adf.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)
                choices = adf.loc[mask, "Objection"]
            else:
                choices = adf["Objection"]
            objection = st.selectbox("Choose an objection:", choices.unique())
            row = adf[adf["Objection"] == objection].iloc[0]

        with right:
            st.markdown("#### 🛠️ Full Rebuttal")
            st.text_area("Rebuttal (copy as needed)", value=row["Rebuttal"], height=140, key="agent_reb_txt")
            colr1, colr2 = st.columns(2)
            with colr1:
                tts_button("Play Rebuttal", row["Rebuttal"], key="agent_rebuttal")
            with colr2:
                copy_button("Rebuttal", row["Rebuttal"], key="agent_rebuttal")

            st.markdown("#### ⚡ One-Liner")
            st.text_area("One-Liner (copy as needed)", value=row["One-Liner"], height=70, key="agent_ol_txt")
            colr3, colr4 = st.columns(2)
            with colr3:
                tts_button("Play One-Liner", row["One-Liner"], key="agent_oneliner")
            with colr4:
                copy_button("One-Liner", row["One-Liner"], key="agent_oneliner")

            st.markdown("#### 📲 SMS Snippet")
            st.text_area("SMS (copy as needed)", value=row["SMS"], height=70, key="agent_sms_txt")
            colr5, colr6 = st.columns(2)
            with colr5:
                tts_button("Play SMS", row["SMS"], key="agent_sms")
            with colr6:
                copy_button("SMS", row["SMS"], key="agent_sms")

            # Optional uploaded audio support
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

# ========== Brokerage Comparison ==========
with tab_brok:
    st.subheader("🏢 Compare Funnel Pilot to Top Brokerages")
    bdf = st.session_state.brokerage_df
    if bdf.empty:
        st.warning("No brokerage dataset found. Place Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx next to this app or upload above.")
    else:
        left, right = st.columns([2, 3])
        with left:
            q2 = st.text_input("Search brokerages / content", "")
            if q2.strip():
                mask2 = bdf.apply(lambda r: r.astype(str).str.contains(q2, case=False).any(), axis=1)
                options = bdf.loc[mask2, "Brokerage"]
            else:
                options = bdf["Brokerage"]
            brokerage = st.selectbox("Select a brokerage:", options.unique())
            rowb = bdf[bdf["Brokerage"] == brokerage].iloc[0]

        with right:
            st.markdown("#### 🛠️ Full Rebuttal")
            st.text_area("Broker Rebuttal (copy as needed)", value=rowb["Funnel Pilot Rebuttal"], height=140, key="brk_reb_txt")
            c1, c2 = st.columns(2)
            with c1:
                tts_button("Play Broker Rebuttal", rowb["Funnel Pilot Rebuttal"], key="broker_rebuttal")
            with c2:
                copy_button("Broker Rebuttal", rowb["Funnel Pilot Rebuttal"], key="broker_rebuttal")

            st.markdown("#### ⚡ One-Liner")
            st.text_area("Broker One-Liner (copy as needed)", value=rowb["One-Liner"], height=70, key="brk_ol_txt")
            c3, c4 = st.columns(2)
            with c3:
                tts_button("Play Broker One-Liner", rowb["One-Liner"], key="broker_oneliner")
            with c4:
                copy_button("Broker One-Liner", rowb["One-Liner"], key="broker_oneliner")

            st.markdown("#### 📲 SMS Snippet")
            st.text_area("Broker SMS (copy as needed)", value=rowb["SMS"], height=70, key="brk_sms_txt")
            c5, c6 = st.columns(2)
            with c5:
                tts_button("Play Broker SMS", rowb["SMS"], key="broker_sms")
            with c6:
                copy_button("Broker SMS", rowb["SMS"], key="broker_sms")

            st.markdown("#### 💥 Power Statement")
            st.text_area("Power Statement (copy as needed)", value=rowb["Power Statement"], height=70, key="brk_power_txt")
            c7, c8 = st.columns(2)
            with c7:
                tts_button("Play Power Statement", rowb["Power Statement"], key="broker_power")
            with c8:
                copy_button("Power Statement", rowb["Power Statement"], key="broker_power")

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

# ========== Favorites ==========
with tab_favs:
    st.subheader("⭐ Your Favorites")
    if not st.session_state.favorites:
        st.info("No favorites yet. Add from the other tabs.")
    else:
        for i, fav in enumerate(st.session_state.favorites):
            with st.container():
                st.markdown(f"### {i+1}. {fav['title']} ({fav['type']})")
                st.markdown(f"**Rebuttal:** {fav['rebuttal']}")
                tts_button("Play", fav['rebuttal'], key=f"fav_rebuttal_{i}")
                copy_button("Rebuttal", fav['rebuttal'], key=f"fav_rebuttal_{i}")

                st.markdown(f"**One-Liner:** {fav['oneliner']}")
                tts_button("Play", fav['oneliner'], key=f"fav_oneliner_{i}")
                copy_button("One-Liner", fav['oneliner'], key=f"fav_oneliner_{i}")

                st.markdown(f"**SMS:** {fav['sms']}")
                tts_button("Play", fav['sms'], key=f"fav_sms_{i}")
                copy_button("SMS", fav['sms'], key=f"fav_sms_{i}")

                if fav.get("power"):
                    st.markdown(f"**Power Statement:** {fav['power']}")
                    tts_button("Play", fav['power'], key=f"fav_power_{i}")
                    copy_button("Power Statement", fav['power'], key=f"fav_power_{i}")

                cols = st.columns([1,1,6])
                with cols[0]:
                    if st.button("🗑️ Remove", key=f"fav_remove_{i}"):
                        st.session_state.favorites.pop(i)
                        st.experimental_rerun()
                st.markdown("---")

        fav_df = pd.DataFrame(st.session_state.favorites)
        st.download_button(
            "⬇️ Download Favorites (Excel)",
            data=df_to_excel_bytes(fav_df),
            file_name="favorites_export.xlsx",
        )
