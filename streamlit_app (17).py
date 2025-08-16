
import hashlib
import json
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------- Config ----------------
CANDIDATE_DATASETS = [
    "Objection_Rebuttal_Master_500 (1).csv",
    "Objection_Rebuttal_Master_500.csv",
    "100_Unique_Objections___Rebuttals - 100_Unique_Objections___Rebuttals.csv (3).csv",
    "100_Unique_Objections___Rebuttals.csv",
    "Agent_Objection_Rebuttals_Dataset_Categorized.csv",
    "training_dataset.csv",
]

BROKERAGE_FILES = [
    "Top_25_Brokerage_Rebuttals_FunnelPilot.xlsx",
]

HEADER_ALIASES = {
    "question": ["objection", "question", "prompt", "q"],
    "answer":   ["rebuttal", "answer", "response", "reply", "script"],
    "category": ["category", "topic"],
    "tags":     ["tags", "keywords", "labels"],
}

BROKER_ALIASES = {
    "brokerage": ["brokerage", "broker", "company", "brand"],
    "rebuttal":  ["rebuttal", "answer", "response", "script"],
    "sms":       ["sms", "text", "text_message"],
    "one_liner": ["one_liner", "one-liner", "oneliner"],
    "notes":     ["notes", "context"],
}

def _find_col(cols: List[str], targets: List[str]):
    low = [str(c).strip().lower() for c in cols]
    for t in targets:
        t = t.lower()
        if t in low:
            return cols[low.index(t)]
    for t in targets:
        t = t.lower()
        for i, c in enumerate(low):
            if t in c:
                return cols[i]
    return None

@st.cache_data(show_spinner=False)
def load_data() -> Tuple[pd.DataFrame, str]:
    base = Path(__file__).parent
    path = None
    for name in CANDIDATE_DATASETS:
        p = base / name
        if p.exists():
            path = p; break
    if path is None:
        raise FileNotFoundError("Place a CSV with columns objection/question and rebuttal/answer next to the app.")

    raw = pd.read_csv(path).dropna(axis=1, how="all")
    q_col = _find_col(list(raw.columns), HEADER_ALIASES["question"])
    a_col = _find_col(list(raw.columns), HEADER_ALIASES["answer"])
    c_col = _find_col(list(raw.columns), HEADER_ALIASES["category"]) or None
    t_col = _find_col(list(raw.columns), HEADER_ALIASES["tags"]) or None
    if q_col is None or a_col is None:
        raise KeyError("Missing objection/question or rebuttal/answer column.")

    df = pd.DataFrame({
        "question": raw[q_col].astype(str).str.strip(),
        "answer": raw[a_col].astype(str).str.strip(),
        "category": raw[c_col].fillna("").astype(str).str.strip() if c_col else "",
        "tags": raw[t_col].fillna("").astype(str).str.strip() if t_col else "",
    })
    df = df[(df["question"] != "") & (df["answer"] != "")].reset_index(drop=True)
    df["rid"] = [hashlib.md5((q + "||" + a).encode("utf-8")).hexdigest()[:16] for q, a in zip(df["question"], df["answer"])]
    return df, path.name

@st.cache_data(show_spinner=False)
def load_brokerage() -> Tuple[pd.DataFrame, str]:
    base = Path(__file__).parent
    path = None
    for name in BROKERAGE_FILES:
        p = base / name
        if p.exists():
            path = p; break
    if path is None:
        raise FileNotFoundError("Add 'Top_25_Brokerage_Rebuttals_FunnelPilot.xlsx' next to the app.")

    xl = pd.ExcelFile(path)
    frames = [xl.parse(s) for s in xl.sheet_names]
    raw = pd.concat(frames, ignore_index=True).dropna(axis=1, how="all")

    b_col = _find_col(list(raw.columns), BROKER_ALIASES["brokerage"])
    r_col = _find_col(list(raw.columns), BROKER_ALIASES["rebuttal"])
    s_col = _find_col(list(raw.columns), BROKER_ALIASES["sms"])
    o_col = _find_col(list(raw.columns), BROKER_ALIASES["one_liner"])
    n_col = _find_col(list(raw.columns), BROKER_ALIASES["notes"])
    if b_col is None or r_col is None:
        raise KeyError("Brokerage workbook needs Brokerage and Rebuttal columns.")

    df = pd.DataFrame({
        "brokerage": raw[b_col].astype(str).str.strip(),
        "rebuttal": raw[r_col].astype(str).str.strip(),
        "sms": raw[s_col].fillna("").astype(str).str.strip() if s_col else "",
        "one_liner": raw[o_col].fillna("").astype(str).str.strip() if o_col else "",
        "notes": raw[n_col].fillna("").astype(str).str.strip() if n_col else "",
    })
    df = df[df["brokerage"] != ""].reset_index(drop=True)
    df["bid"] = [hashlib.md5((b + "||" + r).encode("utf-8")).hexdigest()[:12] for b, r in zip(df["brokerage"], df["rebuttal"])]
    return df, path.name

def copy_button(label: str, text: str, key: str):
    safe = json.dumps(text or "")
    html = f"""
    <button id="{key}" style="padding:6px 10px; font-size:12px; margin-right:6px; cursor:pointer;">{label}</button>
    <script>
    const el_{key.replace("-","_")} = document.getElementById("{key}");
    el_{key.replace("-","_")}.onclick = async () => {{ try {{ await navigator.clipboard.writeText({safe}); }} catch(e){{}} }};
    </script>
    """
    components.html(html, height=40)

def tts_controls(text: str, rate: float, pitch: float, key: str):
    safe = json.dumps(text or "")
    html = f"""
    <div style="display:flex; gap:8px; align-items:center;">
        <button id="{key}-play" style="padding:6px 10px; font-size:12px;">Play</button>
        <button id="{key}-stop" style="padding:6px 10px; font-size:12px;">Stop</button>
    </div>
    <script>
      (function() {{
        const txt = {safe};
        const rate = {rate};
        const pitch = {pitch};
        const makeU = () => {{ const u = new SpeechSynthesisUtterance(txt); u.rate = rate; u.pitch = pitch; return u; }};
        document.getElementById("{key}-play").onclick = () => {{ try {{ speechSynthesis.cancel(); speechSynthesis.speak(makeU()); }} catch(e){{}} }};
        document.getElementById("{key}-stop").onclick = () => {{ try {{ speechSynthesis.cancel(); }} catch(e){{}} }};
      }})();
    </script>
    """
    components.html(html, height=50)

def objections_tab():
    try:
        df, used = load_data()
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        return

    st.write(f"Using dataset: `{used}`")
    term = st.text_input("Search objections", "")
    view = st.radio("View", ["All","Favorites","Most Used"], horizontal=True)

    if "favorites" not in st.session_state: st.session_state.favorites = {}
    if "counts" not in st.session_state: st.session_state.counts = {}

    data = df.copy()
    if term.strip():
        data = data[data["question"].str.lower().str.contains(term.strip().lower())]

    if view == "Favorites":
        data = data[data["rid"].isin(set(st.session_state.favorites.keys()))]
    elif view == "Most Used":
        counts = st.session_state.counts
        ordered = sorted(counts, key=lambda k: counts[k], reverse=True)[:50]
        data = data[data["rid"].isin(ordered)]

    if data.empty: st.warning("No matches."); return

    pick = st.selectbox("Pick", [f"{i}. {q[:90]}" for i, q in enumerate(data["question"].tolist())], index=0)
    idx = int(pick.split(". ",1)[0]); row = data.iloc[idx]
    rid = row["rid"]; st.session_state.counts[rid] = st.session_state.counts.get(rid, 0) + 1

    st.subheader("Objection"); st.write(row["question"])
    st.subheader("Rebuttal"); st.markdown(row["answer"])

    c1, c2, c3 = st.columns(3)
    with c1:
        if rid not in st.session_state.favorites:
            if st.button("Add to Favorites"): st.session_state.favorites[rid] = row.to_dict(); st.rerun()
        else:
            if st.button("Remove Favorite"): st.session_state.favorites.pop(rid,None); st.rerun()
    with c2: copy_button("Copy Rebuttal", row["answer"], key=f"copy-{rid}")
    with c3: st.download_button("Download .txt", row["answer"].encode("utf-8"), "rebuttal.txt", "text/plain")

    st.markdown("---")
    rate = st.slider("Voice speed", 0.6, 1.4, 1.0, 0.05)
    pitch = st.slider("Voice pitch", 0.5, 1.5, 1.0, 0.05)
    tts_controls(row["answer"], rate, pitch, key=f"tts-{rid}")

def brokerage_tab():
    try:
        bdf, used = load_brokerage()
    except Exception as e:
        st.info(f"Brokerage compare not available: {e}")
        return

    st.write(f"Using workbook: `{used}`")
    brokers = sorted(bdf["brokerage"].unique().tolist())
    picked = st.selectbox("Pick a brokerage", brokers, index=0 if brokers else 0)
    compare_fp = st.checkbox("Compare to Funnel Pilot", value=False)

    if not picked: return
    main = bdf[bdf["brokerage"] == picked].iloc[0]

    st.subheader("Primary")
    st.write(f"Brokerage: **{picked}**")
    st.markdown("**Rebuttal**"); st.markdown(main.get("rebuttal","") or "_(none)_")
    st.markdown("**One-liner**"); st.write(main.get("one_liner","") or "_(none)_")
    st.markdown("**SMS**"); st.code(main.get("sms","") or "(none)", language="text")

    c1,c2,c3 = st.columns(3)
    with c1: copy_button("Copy Rebuttal", main.get("rebuttal",""), key=f"b-reb-{main['bid']}")
    with c2: copy_button("Copy SMS", main.get("sms",""), key=f"b-sms-{main['bid']}")
    with c3: copy_button("Copy One-liner", main.get("one_liner",""), key=f"b-one-{main['bid']}")

    st.markdown("---"); st.write("Listen")
    tts_controls(main.get("rebuttal",""), 1.0, 1.0, key=f"tts-b-{main['bid']}")

    pack_text = "\n".join([
        f"Brokerage: {picked}",
        "",
        "Rebuttal:",
        main.get("rebuttal",""),
        "",
        "One-liner:",
        main.get("one_liner",""),
        "",
        "SMS:",
        main.get("sms",""),
        ""
    ])
    st.download_button("Download All (TXT)", pack_text.encode("utf-8"), f"{picked.replace(' ','_')}_pack.txt", "text/plain")

    if compare_fp:
        st.markdown("---"); st.subheader("Compare to Funnel Pilot")
        fp = bdf[bdf["brokerage"].str.lower().str.contains("funnel pilot")]
        if fp.empty:
            st.info("No 'Funnel Pilot' row in workbook.")
        else:
            fp_row = fp.iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Your Pick**")
                st.write(f"Brokerage: **{picked}**")
                st.markdown("**Rebuttal**"); st.markdown(main.get("rebuttal",""))
                st.markdown("**One-liner**"); st.write(main.get("one_liner",""))
                st.markdown("**SMS**"); st.code(main.get("sms",""), language="text")
            with col2:
                st.markdown("**Funnel Pilot**")
                st.markdown("**Rebuttal**"); st.markdown(fp_row.get("rebuttal",""))
                st.markdown("**One-liner**"); st.write(fp_row.get("one_liner",""))
                st.markdown("**SMS**"); st.code(fp_row.get("sms",""), language="text")

            lines = [
                f"Totally hear the appeal of {picked}. Here are a few reasons agents pick Funnel Pilot:",
                "",
                "- Control and ownership: your ads, your CRM, your data.",
                "- Lower lead cost and faster testing to keep CPL efficient.",
                "- Done-for-you setup: domains, A2P, automations, lender co-marketing.",
                "- Weekly coaching and scripts with real-time tweaks.",
                "- Aligned incentives: no platform fee; we win when you close.",
                "",
                "Would it be crazy to run the first 60–90 days with FP, review ROI, and then decide from a position of data?",
            ]
            script = "\n".join(lines)
            st.markdown("**Positioning Script**")
            st.write(script)
            copy_button("Copy Positioning Script", script, key=f"fp-script-{main['bid']}")

def main():
    st.set_page_config(page_title="Pocket Objections — Simple", layout="wide")
    st.title("Pocket Objections — Simple")
    tab1, tab2 = st.tabs(["Objections", "Brokerage Compare"])
    with tab1: objections_tab()
    with tab2: brokerage_tab()

if __name__ == "__main__":
    main()
