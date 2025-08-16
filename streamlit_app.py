
import random
from pathlib import Path
import json
import re
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from collections import Counter

# ---------------- Config ----------------
CANDIDATE_DATASETS = [
    "Objection_Rebuttal_Master_500 (1).csv",
    "Objection_Rebuttal_Master_500.csv",
    "100_Unique_Objections___Rebuttals - 100_Unique_Objections___Rebuttals.csv (3).csv",
    "100_Unique_Objections___Rebuttals.csv",
    "Agent_Objection_Rebuttals_Dataset_Categorized.csv",
    "training_dataset.csv",
]

HEADER_ALIASES = {
    "question": ["objection/question", "objection", "question", "prompt", "q"],
    "answer":   ["rebuttal/answer", "rebuttal", "answer", "response", "reply"],
    "category": ["category", "topic", "bucket"],
    "tags":     ["tags", "keywords", "labels"],
}

TOPIC_SEPARATORS = r"[|;,/]+"

def _lowerstrip(s): 
    return str(s).strip().lower()

def _find_col(cols, targets):
    cols_l = [_lowerstrip(c) for c in cols]
    for t in targets:
        t_l = _lowerstrip(t)
        if t_l in cols_l:
            return cols[cols_l.index(t_l)]
    for t in targets:
        t_l = _lowerstrip(t)
        for i, c in enumerate(cols_l):
            if t_l in c:
                return cols[i]
    return None

def _parse_tokens(cell: str):
    if not isinstance(cell, str) or not cell.strip():
        return []
    tmp = re.split(TOPIC_SEPARATORS, cell)
    return [t.strip() for t in tmp if t.strip()]

def _extract_topic_vocab(df: pd.DataFrame):
    words = []
    if "category" in df.columns:
        words.extend([c for c in df["category"].fillna("").astype(str).str.strip().tolist() if c])
    if "tags" in df.columns:
        for cell in df["tags"].fillna("").astype(str):
            words.extend(_parse_tokens(cell))
    vocab = [w for w in words if 2 <= len(w) <= 40]
    counts = {w.lower():0 for w in vocab}
    for w in vocab:
        counts[w.lower()] += 1
    return [w for w,_ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]

@st.cache_data(show_spinner=False)
def load_data():
    base = Path(__file__).parent
    csv_path = None
    for name in CANDIDATE_DATASETS:
        p = base / name
        if p.exists():
            csv_path = p
            break
    if csv_path is None:
        raise FileNotFoundError(f"Place one of these files next to this app: {', '.join(CANDIDATE_DATASETS)}")

    raw = pd.read_csv(csv_path)
    raw = raw.dropna(axis=1, how="all")
    if raw.empty:
        raise ValueError(f"Dataset '{csv_path.name}' is empty.")

    q_col = _find_col(list(raw.columns), HEADER_ALIASES["question"])
    a_col = _find_col(list(raw.columns), HEADER_ALIASES["answer"])
    c_col = _find_col(list(raw.columns), HEADER_ALIASES["category"])
    t_col = _find_col(list(raw.columns), HEADER_ALIASES["tags"])

    if q_col is None or a_col is None:
        raise KeyError("Dataset needs columns for objection/question and rebuttal/answer.")

    df = pd.DataFrame({
        "question": raw[q_col].astype(str).str.strip(),
        "answer":   raw[a_col].astype(str).str.strip(),
    })
    df["category"] = raw[c_col].fillna("").astype(str).str.strip() if c_col else ""
    df["tags"] = raw[t_col].fillna("").astype(str).str.strip() if t_col else ""

    df = df[(df["question"] != "") & (df["answer"] != "")].reset_index(drop=True)
    topics = _extract_topic_vocab(df)
    return df, csv_path.name, topics

def copy_button(label: str, text: str, key: str):
    safe = json.dumps(text)
    html = f"""
    <button id="{key}" style="padding:6px 10px; font-size:12px; margin-right:6px; cursor:pointer;">
      {label}
    </button>
    <script>
    const btn_{key.replace("-", "_")} = document.getElementById("{key}");
    btn_{key.replace("-", "_")}.onclick = async () => {{
        try {{
            await navigator.clipboard.writeText({safe});
        }} catch (e) {{
            console.log(e);
        }}
    }};
    </script>
    """
    components.html(html, height=40)

def tts_controls(text: str, rate: float, pitch: float, key: str):
    # Use the browser's SpeechSynthesis API (Chrome/Edge/Safari). No external services needed.
    safe = json.dumps(text)
    html = f"""
    <div style="display:flex; gap:8px; align-items:center;">
      <button id="{key}-play" style="padding:6px 10px; font-size:12px; cursor:pointer;">🔊 Play</button>
      <button id="{key}-stop" style="padding:6px 10px; font-size:12px; cursor:pointer;">⏹ Stop</button>
    </div>
    <script>
    (function() {{
        const txt = {safe};
        const rate = {rate};
        const pitch = {pitch};
        const makeUtterance = () => {{
            const u = new SpeechSynthesisUtterance(txt);
            u.rate = rate;
            u.pitch = pitch;
            return u;
        }};
        let current = null;
        const playBtn = document.getElementById("{key}-play");
        const stopBtn = document.getElementById("{key}-stop");
        playBtn.onclick = () => {{
            try {{
                window.speechSynthesis.cancel();
                current = makeUtterance();
                window.speechSynthesis.speak(current);
            }} catch (e) {{ console.log(e); }}
        }};
        stopBtn.onclick = () => {{
            try {{ window.speechSynthesis.cancel(); }} catch (e) {{ console.log(e); }}
        }};
    }})();
    </script>
    """
    components.html(html, height=50)

def main():
    st.set_page_config(page_title="Pocket Objections (Simple)", layout="centered")
    st.title("Pocket Objections — Simple")
    st.caption("Search • Filter • Read or play the rebuttal.")

    try:
        df, used_file, topics = load_data()
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        return

    with st.sidebar:
        st.markdown("### Filters")
        st.write(f"Using: `{used_file}`")
        term = st.text_input("Search in objection", "")

        selected_topics = []
        match_mode = "Any"
        if len(topics) > 0:
            selected_topics = st.multiselect("Topics (from Category/Tags)", options=topics[:200], default=[])
            match_mode = st.radio("Match", options=["Any","All"], horizontal=True, index=0)

        cats = sorted([c for c in df["category"].unique().tolist() if c])
        category = None
        if len(cats) > 0:
            category = st.selectbox("Category", ["All"] + cats, index=0)

        def _parse_all_tags(series):
            acc = set()
            for v in series.fillna("").astype(str):
                for t in _parse_tokens(v):
                    acc.add(t)
            return sorted(acc)

        tag_tokens = _parse_all_tags(df["tags"]) if "tags" in df.columns else []
        tag = None
        if len(tag_tokens) > 0:
            tag = st.selectbox("Tag", ["All"] + tag_tokens, index=0)

        st.markdown("---")
        rate = st.slider("Voice speed", 0.6, 1.4, 1.0, 0.05)
        pitch = st.slider("Voice pitch", 0.5, 1.5, 1.0, 0.05)

    filt = df

    if term.strip():
        tl = term.strip().lower()
        filt = filt[filt["question"].str.lower().str.contains(tl)]

    if selected_topics:
        def has_topics(row):
            bag = set()
            if isinstance(row.get("category",""), str) and row["category"].strip():
                bag.add(row["category"].strip().lower())
            if isinstance(row.get("tags",""), str) and row["tags"].strip():
                bag.update([t.lower() for t in _parse_tokens(row["tags"])])
            targets = [t.lower() for t in selected_topics]
            return all(t in bag for t in targets) if match_mode == "All" else any(t in bag for t in targets)
        filt = filt[filt.apply(has_topics, axis=1)]

    if category and category != "All":
        filt = filt[filt["category"] == category]

    if tag and tag != "All":
        def has_tag(cell: str) -> bool:
            cell = (cell or "").lower().replace("|", ",").replace(";", ",")
            toks = [t.strip() for t in cell.split(",") if t.strip()]
            return tag.lower() in toks
        filt = filt[filt["tags"].apply(has_tag)]

    count = len(filt)
    st.write(f"Matches: **{count}**")
    if count == 0:
        st.warning("No results. Try clearing filters or a different search.")
        return

    options = [f"{i}. {q[:120]}" for i, q in enumerate(filt['question'].tolist())]
    selected = st.selectbox("Pick an objection", options, index=0, label_visibility="collapsed")
    sel_idx = int(selected.split(". ", 1)[0])
    row = filt.iloc[sel_idx]

    st.subheader("Objection")
    if row["category"]:
        st.write(f"**Category:** {row['category']}")
    st.write(row["question"])

    st.subheader("Rebuttal")
    st.markdown(row["answer"])

    # Quick actions: Copy/Download rebuttal
    st.markdown("---")
    st.subheader("Quick actions")
    copy_button("Copy Rebuttal", row["answer"], key="copy-rebuttal")
    st.download_button("Download Rebuttal.txt", data=row["answer"].encode("utf-8"),
                       file_name="rebuttal.txt", mime="text/plain")

    # New: Play audio (browser TTS)
    st.markdown("---")
    st.subheader("Listen")
    st.caption("Uses your browser's built‑in voice (no upload). If you don't hear anything, ensure sound is on and the tab is active.")
    tts_controls(row["answer"], rate=rate, pitch=pitch, key="tts1")

    st.caption("Empathy → short frame → value → tie‑down → next step.")

if __name__ == "__main__":
    main()
