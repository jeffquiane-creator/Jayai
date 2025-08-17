# streamlit_app.py — Simple, stable version
# Views: Agent Objections | Brokerage Comparison
# Audio: browser TTS (no pyttsx3/gTTS). Copy buttons included. No Excel export.

import streamlit as st
import pandas as pd
import os, glob, json
import streamlit.components.v1 as components

st.set_page_config(page_title="Funnel Pilot (Simple)", layout="wide")
st.title("🎯 Funnel Pilot — Agent Objections & Brokerage Comparison")

# ---------- Small helpers ----------
def tts_button(label: str, text: str, key: str, rate=1.0, pitch=1.0, volume=1.0):
    """Browser Text-to-Speech play button (no server dependencies)."""
    safe_text  = json.dumps(str(text or ""))
    safe_rate  = json.dumps(float(rate))
    safe_pitch = json.dumps(float(pitch))
    safe_vol   = json.dumps(float(volume))
    btn_id = f"tts_{key}"
    html = f"""
    <button id='{btn_id}' style='padding:8px 12px;border-radius:8px;border:1px solid #444;cursor:pointer;margin:6px 8px 0 0'>
      ▶️ {label}
    </button>
    <script>
      const el_{btn_id} = document.getElementById('{btn_id}');
      if (el_{btn_id}) {{
        el_{btn_id}.onclick = () => {{
          try {{
            const u = new SpeechSynthesisUtterance({safe_text});
            u.rate   = {safe_rate};
            u.pitch  = {safe_pitch};
            u.volume = {safe_vol};
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
          }} catch(e) {{ alert("Text-to-speech not available in this browser."); }}
        }};
      }}
    </script>
    """
    components.html(html, height=48)

def copy_button(label: str, text: str, key: str):
    safe_text = json.dumps(str(text or ""))
    btn_id = f"copy_{key}"
    html = f"""
    <button id='{btn_id}' style='padding:8px 10px;border-radius:8px;border:1px solid #444;cursor:pointer;margin:6px 0 0 0'>
      📋 Copy {label}
    </button>
    <script>
      const btn_{btn_id} = document.getElementById('{btn_id}');
      if (btn_{btn_id} && navigator.clipboard) {{
        btn_{btn_id}.onclick = async () => {{
          try {{ await navigator.clipboard.writeText({safe_text}); }}
          catch (e) {{ alert('Copy blocked by browser; select and copy manually.'); }}
        }};
      }}
    </script>
    """
    components.html(html, height=42)

def try_read(path: str):
    """Read CSV first; XLSX if available and openpyxl exists. Return df or None."""
    try:
        if path.lower().endswith(".csv"):
            return pd.read_csv(path)
        elif path.lower().endswith(".xlsx"):
            # reading xlsx requires openpyxl; if not installed, this will raise and we ignore
            return pd.read_excel(path)
    except Exception:
        return None
    return None

def autodetect_agent_df():
    # Prefer CSV to avoid openpyxl
    candidates = [
        "Agent_Objections_Rebuttals.csv",
        "Objection_Rebuttal_Master_500 (1).csv",
        "Objection_Rebuttal_Master_500.csv",
        "Agent_Objections_Rebuttals.xlsx",
        "Objection_Rebuttal_Master_500.xlsx",
    ] + sorted(glob.glob("*.csv")) + sorted(glob.glob("*.xlsx"))
    for p in candidates:
        if not os.path.exists(p): 
            continue
        df = try_read(p)
        if df is not None and {"Objection","Rebuttal"}.issubset(set(map(str, df.columns))):
            # Normalize column names
            cols = {c.lower(): c for c in df.columns}
            df = df.rename(columns={
                cols.get("objection","Objection"): "Objection",
                cols.get("rebuttal","Rebuttal"):   "Rebuttal",
                cols.get("one-liner","One-Liner"): "One-Liner",
                cols.get("sms","SMS"):             "SMS",
            })
            return df, p
    return pd.DataFrame(columns=["Objection","Rebuttal","One-Liner","SMS"]), None

def autodetect_broker_df():
    candidates = [
        "Top_25_Brokerage_Rebuttals_FunnelPilot.csv",
        "Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.csv",
        "Top_25_Brokerage_Rebuttals_FunnelPilot.xlsx",
        "Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx",
    ] + sorted(glob.glob("*.csv")) + sorted(glob.glob("*.xlsx"))
    for p in candidates:
        if not os.path.exists(p):
            continue
        df = try_read(p)
        if df is not None and "Brokerage" in df.columns:
            # Normalize expected columns if present
            rename_map = {}
            for want in ["Funnel Pilot Rebuttal","One-Liner","SMS","Power Statement"]:
                # best-effort: case insensitive
                found = [c for c in df.columns if c.strip().lower() == want.lower()]
                if found: rename_map[found[0]] = want
                else: df[want] = ""
            df = df.rename(columns=rename_map)
            return df[["Brokerage","Funnel Pilot Rebuttal","One-Liner","SMS","Power Statement"]], p
    return pd.DataFrame(columns=["Brokerage","Funnel Pilot Rebuttal","One-Liner","SMS","Power Statement"]), None

# ---------- Audio controls (global) ----------
with st.sidebar:
    st.markdown("### 🔊 Audio")
    rate  = st.slider("Speed", 0.5, 2.0, 1.0, 0.05)
    pitch = st.slider("Pitch", 0.5, 2.0, 1.0, 0.05)
    vol   = st.slider("Volume", 0.0, 1.0, 1.0, 0.05)

# ---------- Load data (auto + optional upload) ----------
if "agent_df" not in st.session_state:
    st.session_state.agent_df, st.session_state.agent_path = autodetect_agent_df()
if "broker_df" not in st.session_state:
    st.session_state.broker_df, st.session_state.broker_path = autodetect_broker_df()

with st.expander("📦 Data • Upload (optional)"):
    c1, c2 = st.columns(2)
    with c1:
        st.caption(f"Agent file: **{st.session_state.agent_path or 'not detected'}**")
        up_a = st.file_uploader("Upload Agent Objections (CSV/XLSX)", type=["csv","xlsx"], key="up_agent")
        if up_a is not None:
            try:
                df = pd.read_csv(up_a) if up_a.name.lower().endswith(".csv") else pd.read_excel(up_a)
                if {"Objection","Rebuttal"}.issubset(set(map(str, df.columns))):
                    # Normalize
                    cols = {c.lower(): c for c in df.columns}
                    df = df.rename(columns={
                        cols.get("objection","Objection"): "Objection",
                        cols.get("rebuttal","Rebuttal"):   "Rebuttal",
                        cols.get("one-liner","One-Liner"): "One-Liner",
                        cols.get("sms","SMS"):             "SMS",
                    })
                    st.session_state.agent_df = df[["Objection","Rebuttal","One-Liner","SMS"]]
                    st.session_state.agent_path = up_a.name
                    st.success(f"Loaded: {up_a.name}")
                else:
                    st.error("File must include Objection and Rebuttal columns.")
            except Exception as e:
                st.error(f"Could not read file: {e}")
    with c2:
        st.caption(f"Broker file: **{st.session_state.broker_path or 'not detected'}**")
        up_b = st.file_uploader("Upload Brokerage Comparison (CSV/XLSX)", type=["csv","xlsx"], key="up_broker")
        if up_b is not None:
            try:
                df = pd.read_csv(up_b) if up_b.name.lower().endswith(".csv") else pd.read_excel(up_b)
                if "Brokerage" in df.columns:
                    for col in ["Funnel Pilot Rebuttal","One-Liner","SMS","Power Statement"]:
                        if col not in df.columns: df[col] = ""
                    st.session_state.broker_df = df[["Brokerage","Funnel Pilot Rebuttal","One-Liner","SMS","Power Statement"]]
                    st.session_state.broker_path = up_b.name
                    st.success(f"Loaded: {up_b.name}")
                else:
                    st.error("File must include a Brokerage column.")
            except Exception as e:
                st.error(f"Could not read file: {e}")

# ---------- Top nav ----------
mode = st.radio("Navigate:", ["🙋 Agent Objections", "🏢 Brokerage Comparison"], horizontal=True)

# ---------- Agent Objections ----------
if mode == "🙋 Agent Objections":
    adf = st.session_state.agent_df
    if adf.empty:
        st.warning("No agent objection data found. Upload or place a CSV like 'Objection_Rebuttal_Master_500 (1).csv' in the repo.")
    else:
        q = st.text_input("Search objections / rebuttals / SMS", "")
        if q.strip():
            show_df = adf[adf.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)].reset_index(drop=True)
        else:
            show_df = adf.reset_index(drop=True)

        options = show_df["Objection"].tolist()
        selected = st.radio("Choose an objection:", options, key="obj_radio")

        if selected:
            row = show_df[show_df["Objection"] == selected].iloc[0]
            st.markdown("#### 💡 Rebuttal")
            st.write(row.get("Rebuttal",""))
            col1, col2 = st.columns(2)
            with col1:
                tts_button("Play Rebuttal", row.get("Rebuttal",""), key="obj_reb", rate=rate, pitch=pitch, volume=vol)
            with col2:
                copy_button("Rebuttal", row.get("Rebuttal",""), key="obj_reb")

            if str(row.get("One-Liner","")).strip():
                st.markdown("#### ⚡ One-Liner")
                st.write(row["One-Liner"])
                col3, col4 = st.columns(2)
                with col3:
                    tts_button("Play One-Liner", row["One-Liner"], key="obj_ol", rate=rate, pitch=pitch, volume=vol)
                with col4:
                    copy_button("One-Liner", row["One-Liner"], key="obj_ol")

            if str(row.get("SMS","")).strip():
                st.markdown("#### 📲 SMS")
                st.write(row["SMS"])
                col5, col6 = st.columns(2)
                with col5:
                    tts_button("Play SMS", row["SMS"], key="obj_sms", rate=rate, pitch=pitch, volume=vol)
                with col6:
                    copy_button("SMS", row["SMS"], key="obj_sms")

# ---------- Brokerage Comparison ----------
if mode == "🏢 Brokerage Comparison":
    bdf = st.session_state.broker_df
    if bdf.empty:
        st.warning("No brokerage data found. Upload or place one of the Top_25_* files in the repo (CSV preferred).")
    else:
        q2 = st.text_input("Search brokerages / content", "")
        if q2.strip():
            show_b = bdf[bdf.apply(lambda r: r.astype(str).str.contains(q2, case=False).any(), axis=1)].reset_index(drop=True)
        else:
            show_b = bdf.reset_index(drop=True)

        options_b = show_b["Brokerage"].tolist()
        selected_b = st.radio("Select a brokerage:", options_b, key="bro_radio")

        if selected_b:
            rowb = show_b[show_b["Brokerage"] == selected_b].iloc[0]

            st.markdown("#### 💡 Rebuttal")
            st.write(rowb.get("Funnel Pilot Rebuttal",""))
            c1, c2 = st.columns(2)
            with c1:
                tts_button("Play Rebuttal", rowb.get("Funnel Pilot Rebuttal",""), key="bro_reb", rate=rate, pitch=pitch, volume=vol)
            with c2:
                copy_button("Rebuttal", rowb.get("Funnel Pilot Rebuttal",""), key="bro_reb")

            if str(rowb.get("One-Liner","")).strip():
                st.markdown("#### ⚡ One-Liner")
                st.write(rowb["One-Liner"])
                c3, c4 = st.columns(2)
                with c3:
                    tts_button("Play One-Liner", rowb["One-Liner"], key="bro_ol", rate=rate, pitch=pitch, volume=vol)
                with c4:
                    copy_button("One-Liner", rowb["One-Liner"], key="bro_ol")

            if str(rowb.get("SMS","")).strip():
                st.markdown("#### 📲 SMS")
                st.write(rowb["SMS"])
                c5, c6 = st.columns(2)
                with c5:
                    tts_button("Play SMS", rowb["SMS"], key="bro_sms", rate=rate, pitch=pitch, volume=vol)
                with c6:
                    copy_button("SMS", rowb["SMS"], key="bro_sms")

            if str(rowb.get("Power Statement","")).strip():
                st.markdown("#### 💥 Power Statement")
                st.write(rowb["Power Statement"])
                c7, c8 = st.columns(2)
                with c7:
                    tts_button("Play Power", rowb["Power Statement"], key="bro_power", rate=rate, pitch=pitch, volume=vol)
                with c8:
                    copy_button("Power", rowb["Power Statement"], key="bro_power")

