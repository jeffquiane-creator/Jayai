# app.py — Funnel Pilot Hub (auto-detect datasets + full features)
# Works with: Agent_Objections_Rebuttals.xlsx/.csv, Objection_Rebuttal_Master_500 (1).csv, etc.
#             Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx (or CSV) and
#             Top_25_Brokerage_Rebuttals_FunnelPilot.xlsx
# No pyttsx3; audio is browser TTS with rate/pitch/volume controls.

import streamlit as st
import pandas as pd
import os, io, json, math, re, glob
import streamlit.components.v1 as components

# ---------- Tiny UI helpers ----------
def tts_button(label, text, key, rate=1.0, pitch=1.0, volume=1.0):
    safe_text  = json.dumps(str(text))
    safe_rate  = json.dumps(float(rate))
    safe_pitch = json.dumps(float(pitch))
    safe_vol   = json.dumps(float(volume))
    btn_id = f"tts_{key}"
    html = f"""
    <button id='{btn_id}' style='padding:8px 12px;border-radius:10px;border:1px solid #444;cursor:pointer;margin:6px 6px 0 0'>
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

def copy_button(label, text, key):
    safe_text = json.dumps(str(text))
    btn_id = f"copy_{key}"
    html = f"""
    <button id='{btn_id}' style='padding:8px 10px;border-radius:10px;border:1px solid #444;cursor:pointer;margin:6px 0 0 6px'>
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

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()

# ---------- Column contracts ----------
BROKERAGE_COLS = ["Brokerage", "Funnel Pilot Rebuttal", "One-Liner", "SMS", "Power Statement"]
AGENT_COLS     = ["Objection", "Rebuttal", "One-Liner", "SMS", "AudioPath"]

# ---------- Discovery helpers ----------
def try_load(path: str) -> pd.DataFrame | None:
    try:
        if path.lower().endswith(".csv"):
            return pd.read_csv(path)
        elif path.lower().endswith(".xlsx"):
            return pd.read_excel(path)
        else:
            return None
    except Exception:
        return None

def ensure_cols(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]

def discover_dataset(expected_cols: list[str], preferred_names: list[str], min_required: list[str]):
    """
    Returns (df, path, found_candidates)
    - preferred_names are tried first if present
    - then any *.xlsx/*.csv in cwd; we pick the first that has all min_required cols
    """
    cwd_files = set(glob.glob("*.xlsx") + glob.glob("*.csv"))
    candidates = [p for p in preferred_names if os.path.exists(p)]
    # Add all others, sorted by filename, but keep uniqueness
    for f in sorted(cwd_files):
        if f not in candidates:
            candidates.append(f)

    found_list = []
    for p in candidates:
        df = try_load(p)
        if df is None:
            continue
        found_list.append(p)
        lower = [c.strip().lower() for c in df.columns]
        if all(mr.lower() in lower for mr in min_required):
            return ensure_cols(df, expected_cols), p, found_list

    # Nothing matched min_required; return empty with list of what we saw
    return pd.DataFrame(columns=expected_cols), None, found_list

# ---------- Page setup ----------
st.set_page_config(page_title="Funnel Pilot Hub", layout="wide")
st.title("🚀 Funnel Pilot Rebuttal & Brokerage Hub")

# Global audio controls (for all ▶️)
with st.sidebar:
    st.markdown("### 🔊 Audio Controls")
    rate  = st.slider("Speed (rate)", 0.5, 2.0, 1.0, 0.05)
    pitch = st.slider("Tempo (pitch)", 0.5, 2.0, 1.0, 0.05)
    vol   = st.slider("Volume", 0.0, 1.0, 1.0, 0.05)
    st.caption("These apply to every ▶️ Play button in the app.")

# ---------- Initial auto-detect (once) ----------
if "agent_df" not in st.session_state or "agent_path" not in st.session_state:
    agent_df, agent_path, agent_seen = discover_dataset(
        AGENT_COLS,
        preferred_names=[
            "Agent_Objections_Rebuttals.xlsx",
            "Agent_Objections_Rebuttals.csv",
            "Objection_Rebuttal_Master_500 (1).csv",
            "Objection_Rebuttal_Master_500.csv",
            "Objection_Rebuttal_Master_500.xlsx",
        ],
        min_required=["Objection","Rebuttal"]
    )
    st.session_state.agent_df = agent_df
    st.session_state.agent_path = agent_path
    st.session_state.agent_seen = agent_seen

if "brokerage_df" not in st.session_state or "brokerage_path" not in st.session_state:
    brokerage_df, brokerage_path, brokerage_seen = discover_dataset(
        BROKERAGE_COLS,
        preferred_names=[
            "Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.xlsx",
            "Top_25_Brokerage_Rebuttals_Final_with_Power_Statements.csv",
            "Top_25_Brokerage_Rebuttals_FunnelPilot.xlsx",
            "Top_25_Brokerage_Rebuttals_FunnelPilot.csv",
        ],
        min_required=["Brokerage"]
    )
    st.session_state.brokerage_df = brokerage_df
    st.session_state.brokerage_path = brokerage_path
    st.session_state.brokerage_seen = brokerage_seen

if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "builder_rows" not in st.session_state:
    st.session_state.builder_rows = []

# ---------- Data sources / upload ----------
with st.expander("📦 Data Sources • Upload / Export"):
    c1, c2 = st.columns(2)

    with c1:
        st.caption("**Brokerage Comparisons**")
        st.write("Loaded file:", st.session_state.brokerage_path or "— not detected —")
        if st.session_state.get("brokerage_seen"):
            st.caption("Files scanned: " + ", ".join(st.session_state.brokerage_seen))
        up_b = st.file_uploader("Upload Brokerage (xlsx/csv)", type=["xlsx","csv"], key="up_broker")
        if up_b is not None:
            try:
                bdf = pd.read_csv(up_b) if up_b.name.lower().endswith(".csv") else pd.read_excel(up_b)
                st.session_state.brokerage_df = ensure_cols(bdf, BROKERAGE_COLS)
                st.session_state.brokerage_path = up_b.name
                st.success(f"Loaded: {up_b.name}")
            except Exception as e:
                st.error(f"Failed to load brokerage file: {e}")
        st.download_button(
            "⬇️ Download Current Brokerage Dataset (Excel)",
            data=df_to_excel_bytes(st.session_state.brokerage_df),
            file_name="brokerage_dataset_current.xlsx",
        )

    with c2:
        st.caption("**Agent Objections**")
        st.write("Loaded file:", st.session_state.agent_path or "— not detected —")
        if st.session_state.get("agent_seen"):
            st.caption("Files scanned: " + ", ".join(st.session_state.agent_seen))
        up_a = st.file_uploader("Upload Agent Objections (xlsx/csv)", type=["xlsx","csv"], key="up_agent")
        if up_a is not None:
            try:
                adf = pd.read_csv(up_a) if up_a.name.lower().endswith(".csv") else pd.read_excel(up_a)
                st.session_state.agent_df = ensure_cols(adf, AGENT_COLS)
                st.session_state.agent_path = up_a.name
                st.success(f"Loaded: {up_a.name}")
            except Exception as e:
                st.error(f"Failed to load agent objections file: {e}")
        st.download_button(
            "⬇️ Download Current Agent Dataset (Excel)",
            data=df_to_excel_bytes(st.session_state.agent_df),
            file_name="agent_objections_current.xlsx",
        )

# ---------- Top nav ----------
mode = st.radio(
    "Navigate:",
    ["🙋 Agent Objections", "🏢 Brokerage Comparison", "⭐ Favorites", "📥 Build Dataset"],
    horizontal=True
)

# ---------- Agent Objections ----------
if mode == "🙋 Agent Objections":
    st.subheader("🙋 Agent Objection Handling")

    adf = st.session_state.agent_df
    if adf.empty:
        st.warning("No agent objection data found. Use the expander above to upload/select your dataset.")
    else:
        left, right = st.columns([2, 3])
        with left:
            q = st.text_input("Search objections / one-liners / SMS", "")
            filtered = (
                adf[adf.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)]
                if q.strip() else adf
            ).reset_index(drop=True)

            per_page = st.selectbox("Items per page", [10, 20, 30, 50, 100], index=2)
            total_pages = max(1, math.ceil(len(filtered) / per_page))
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key="obj_page")
            start, end = (page-1)*per_page, (page-1)*per_page + per_page
            page_df = filtered.iloc[start:end]

            options = page_df["Objection"].tolist()
            if not options:
                st.info("No results. Try a different search.")
                selected_objection = None
            else:
                selected_objection = st.radio("Choose an objection:", options, key=f"objection_radio_{page}")

        with right:
            if selected_objection is not None:
                row = adf[adf["Objection"] == selected_objection].iloc[0]

                st.markdown("#### 🛠️ Full Rebuttal")
                st.text_area("Rebuttal (copy as needed)", value=row["Rebuttal"], height=140, key="agent_reb_txt")
                c1, c2 = st.columns(2)
                with c1:
                    tts_button("Play Rebuttal", row["Rebuttal"], key="agent_reb", rate=rate, pitch=pitch, volume=vol)
                with c2:
                    copy_button("Rebuttal", row["Rebuttal"], key="agent_reb")

                st.markdown("#### ⚡ One-Liner")
                st.text_area("One-Liner (copy as needed)", value=row["One-Liner"], height=70, key="agent_ol_txt")
                c3, c4 = st.columns(2)
                with c3:
                    tts_button("Play One-Liner", row["One-Liner"], key="agent_ol", rate=rate, pitch=pitch, volume=vol)
                with c4:
                    copy_button("One-Liner", row["One-Liner"], key="agent_ol")

                st.markdown("#### 📲 SMS Snippet")
                st.text_area("SMS (copy as needed)", value=row["SMS"], height=70, key="agent_sms_txt")
                c5, c6 = st.columns(2)
                with c5:
                    tts_button("Play SMS", row["SMS"], key="agent_sms", rate=rate, pitch=pitch, volume=vol)
                with c6:
                    copy_button("SMS", row["SMS"], key="agent_sms")

                # Optional local audio file support
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

# ---------- Brokerage Comparison ----------
elif mode == "🏢 Brokerage Comparison":
    st.subheader("🏢 Compare Funnel Pilot to Top Brokerages")
    bdf = st.session_state.brokerage_df
    if bdf.empty:
        st.warning("No brokerage dataset found. Use the expander above to upload/select your dataset.")
    else:
        left, right = st.columns([2, 3])
        with left:
            q2 = st.text_input("Search brokerages / content", "")
            filtered_b = (
                bdf[bdf.apply(lambda r: r.astype(str).str.contains(q2, case=False).any(), axis=1)]
                if q2.strip() else bdf
            ).reset_index(drop=True)

            per_page_b = st.selectbox("Items per page ", [10, 20, 30, 50, 100], index=2, key="brok_per_page")
            total_pages_b = max(1, math.ceil(len(filtered_b) / per_page_b))
            page_b = st.number_input("Page ", min_value=1, max_value=total_pages_b, value=1, step=1, key="broker_page")
            start_b, end_b = (page_b-1)*per_page_b, (page_b-1)*per_page_b + per_page_b
            page_df_b = filtered_b.iloc[start_b:end_b]

            options_b = page_df_b["Brokerage"].tolist()
            if not options_b:
                st.info("No results. Try a different search.")
                selected_brokerage = None
            else:
                selected_brokerage = st.radio("Select a brokerage:", options_b, key=f"broker_radio_{page_b}")

        with right:
            if selected_brokerage is not None:
                rowb = bdf[bdf["Brokerage"] == selected_brokerage].iloc[0]

                st.markdown("#### 🛠️ Full Rebuttal")
                st.text_area("Broker Rebuttal (copy as needed)", value=rowb["Funnel Pilot Rebuttal"], height=140, key="brk_reb_txt")
                c1, c2 = st.columns(2)
                with c1:
                    tts_button("Play Broker Rebuttal", rowb["Funnel Pilot Rebuttal"], key="broker_reb", rate=rate, pitch=pitch, volume=vol)
                with c2:
                    copy_button("Broker Rebuttal", rowb["Funnel Pilot Rebuttal"], key="broker_reb")

                st.markdown("#### ⚡ One-Liner")
                st.text_area("Broker One-Liner (copy as needed)", value=rowb["One-Liner"], height=70, key="brk_ol_txt")
                c3, c4 = st.columns(2)
                with c3:
                    tts_button("Play Broker One-Liner", rowb["One-Liner"], key="broker_ol", rate=rate, pitch=pitch, volume=vol)
                with c4:
                    copy_button("Broker One-Liner", rowb["One-Liner"], key="broker_ol")

                st.markdown("#### 📲 SMS Snippet")
                st.text_area("Broker SMS (copy as needed)", value=rowb["SMS"], height=70, key="brk_sms_txt")
                c5, c6 = st.columns(2)
                with c5:
                    tts_button("Play Broker SMS", rowb["SMS"], key="broker_sms", rate=rate, pitch=pitch, volume=vol)
                with c6:
                    copy_button("Broker SMS", rowb["SMS"], key="broker_sms")

                st.markdown("#### 💥 Power Statement")
                st.text_area("Power Statement (copy as needed)", value=rowb["Power Statement"], height=70, key="brk_power_txt")
                c7, c8 = st.columns(2)
                with c7:
                    tts_button("Play Power Statement", rowb["Power Statement"], key="broker_power", rate=rate, pitch=pitch, volume=vol)
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

# ---------- Favorites ----------
elif mode == "⭐ Favorites":
    st.subheader("⭐ Your Favorites")
    if not st.session_state.favorites:
        st.info("No favorites yet. Add from the other views.")
    else:
        for i, fav in enumerate(st.session_state.favorites):
            with st.container():
                st.markdown(f"### {i+1}. {fav['title']} ({fav['type']})")
                st.markdown("**Rebuttal:**")
                st.write(fav["rebuttal"])
                tts_button("Play", fav["rebuttal"], key=f"fav_reb_{i}", rate=rate, pitch=pitch, volume=vol)
                copy_button("Rebuttal", fav["rebuttal"], key=f"fav_reb_{i}")

                st.markdown("**One-Liner:**")
                st.write(fav["oneliner"])
                tts_button("Play", fav["oneliner"], key=f"fav_ol_{i}", rate=rate, pitch=pitch, volume=vol)
                copy_button("One-Liner", fav["oneliner"], key=f"fav_ol_{i}")

                st.markdown("**SMS:**")
                st.write(fav["sms"])
                tts_button("Play", fav["sms"], key=f"fav_sms_{i}", rate=rate, pitch=pitch, volume=vol)
                copy_button("SMS", fav["sms"], key=f"fav_sms_{i}")

                if fav.get("power"):
                    st.markdown("**Power Statement:**")
                    st.write(fav["power"])
                    tts_button("Play", fav["power"], key=f"fav_power_{i}", rate=rate, pitch=pitch, volume=vol)
                    copy_button("Power Statement", fav["power"], key=f"fav_power_{i}")

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

# ---------- Build Dataset (from transcripts) ----------
elif mode == "📥 Build Dataset":
    st.subheader("📥 Build Agent_Objections_Rebuttals from Transcript .txt files")
    st.caption("Upload one or more .txt transcripts. We’ll guess objection/rebuttal pairs; you can edit and export.")
    uploaded_txts = st.file_uploader("Upload transcript .txt files", type=["txt"], accept_multiple_files=True)

    def split_paragraphs(text: str):
        parts = re.split(r"\n\s*\n", text.strip())
        return [p.strip() for p in parts if p.strip()]

    def guess_pairs(paragraphs):
        pairs = []
        i = 0
        while i < len(paragraphs):
            p = paragraphs[i]
            lower = p.lower()
            is_obj = (
                lower.startswith("objection:")
                or p.strip().endswith("?")
                or any(k in lower for k in ["concern", "worried", "worry", "hesitant", "i don't", "i do not", "i'm not sure", "hesitation"])
            )
            if is_obj and i + 1 < len(paragraphs):
                obj = re.sub(r"^objection:\s*", "", p, flags=re.I).strip()
                reb = paragraphs[i + 1].strip()
                pairs.append({"Objection": obj, "Rebuttal": reb, "One-Liner": "", "SMS": "", "AudioPath": ""})
                i += 2
            else:
                i += 1
        return pairs

    if uploaded_txts:
        for uf in uploaded_txts:
            text = uf.read().decode(errors="ignore")
            paras = split_paragraphs(text)
            candidates = guess_pairs(paras)
            if not candidates:
                st.info(f"No obvious objection/rebuttal pairs found in **{uf.name}**.")
            else:
                st.success(f"Found {len(candidates)} candidate pairs in **{uf.name}**.")
                st.session_state.builder_rows.extend(candidates)

    st.markdown("### ✍️ Review & Edit Pairs")
    if not st.session_state.builder_rows:
        st.info("No rows yet. Upload .txt files above, or add manually below.")
    add_cols = st.columns([4,4,3,1])
    with add_cols[0]:
        new_obj = st.text_input("Objection (manual add)", key="manual_obj")
    with add_cols[1]:
        new_reb = st.text_area("Rebuttal (manual add)", height=80, key="manual_reb")
    with add_cols[2]:
        new_ol  = st.text_input("One-Liner (optional)", key="manual_ol")
        new_sms = st.text_input("SMS (optional)", key="manual_sms")
    with add_cols[3]:
        if st.button("➕ Add"):
            if new_obj.strip() and new_reb.strip():
                st.session_state.builder_rows.append(
                    {"Objection": new_obj.strip(), "Rebuttal": new_reb.strip(),
                     "One-Liner": new_ol.strip(), "SMS": new_sms.strip(), "AudioPath": ""}
                )
                st.success("Added.")
            else:
                st.warning("Objection and Rebuttal required.")

    # editable blocks + delete
    to_remove = []
    for idx, row in enumerate(st.session_state.builder_rows):
        with st.expander(f"{idx+1}. {row['Objection'][:90]}"):
            c1,c2 = st.columns(2)
            with c1:
                row["Objection"] = st.text_area("Objection", value=row["Objection"], key=f"e_obj_{idx}", height=90)
                row["One-Liner"] = st.text_input("One-Liner", value=row.get("One-Liner",""), key=f"e_ol_{idx}")
                row["SMS"]       = st.text_input("SMS",       value=row.get("SMS",""), key=f"e_sms_{idx}")
            with c2:
                row["Rebuttal"]  = st.text_area("Rebuttal", value=row["Rebuttal"], key=f"e_reb_{idx}", height=150)
                tts_button("Play Rebuttal", row["Rebuttal"], key=f"e_reb_play_{idx}", rate=rate, pitch=pitch, volume=vol)
                copy_button("Rebuttal", row["Rebuttal"], key=f"e_reb_copy_{idx}")
            col_del, _ = st.columns([1,9])
            with col_del:
                if st.button("🗑️ Delete", key=f"del_{idx}"):
                    to_remove.append(idx)

    if to_remove:
        for i in sorted(to_remove, reverse=True):
            st.session_state.builder_rows.pop(i)
        st.success("Removed selected rows.")

    if st.session_state.builder_rows:
        out_df = pd.DataFrame(st.session_state.builder_rows, columns=AGENT_COLS)
        st.markdown("### 📤 Export")
        st.download_button("⬇️ Download CSV", data=out_df.to_csv(index=False).encode(), file_name="Agent_Objections_Rebuttals.csv", mime="text/csv")
        st.download_button("⬇️ Download Excel", data=df_to_excel_bytes(out_df), file_name="Agent_Objections_Rebuttals.xlsx")
        if st.button("📥 Load into App"):
            st.session_state.agent_df = out_df[AGENT_COLS]
            st.success("Loaded into the app. Switch to ‘🙋 Agent Objections’.")
