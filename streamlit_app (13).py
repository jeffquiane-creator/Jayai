from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
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
    "Top_25_Brokerage_Rebuttals.xlsx",
    "Brokerage_Rebuttals.xlsx",
]

HEADER_ALIASES = {
    "question": ["objection/question", "objection", "question", "prompt", "q"],
    "answer":   ["rebuttal/answer", "rebuttal", "answer", "response", "reply", "script"],
    "category": ["category", "topic", "bucket"],
    "tags":     ["tags", "keywords", "labels"],
}

BROKER_ALIASES = {
    "brokerage": ["brokerage", "broker", "company", "brand", "target_brokerage"],
    "rebuttal":  ["rebuttal", "answer", "response", "script", "talk_track", "talking_points"],
    "sms":       ["sms", "sms_copy", "text", "text_message"],
    "one_liner": ["one_liner", "one-liner", "oneliner", "soundbite", "hook"],
    "notes":     ["notes", "context", "angle", "why_this_works"],
}

TOPIC_SEPARATORS = r"[|;,/]+"


def _lowerstrip(s):
    return str(s).strip().lower()


def _find_col(cols: List[str], targets: List[str]):
    cols_l = [_lowerstrip(c) for c in cols]
    # exact match first
    for t in targets:
        t_l = _lowerstrip(t)
        if t_l in cols_l:
            return cols[cols_l.index(t_l)]
    # soft contains match
    for t in targets:
        t_l = _lowerstrip(t)
        for i, c in enumerate(cols_l):
            if t_l in c:
                return cols[i]
    return None


def _parse_tokens(cell: str) -> List[str]:
    if not isinstance(cell, str) or not cell.strip():
        return []
    tmp = re.split(TOPIC_SEPARATORS, cell)
    return [t.strip() for t in tmp if t.strip()]


def _extract_topic_vocab(df: pd.DataFrame) -> List[str]:
    words = []
    if "category" in df.columns:
        words.extend([c for c in df["category"].fillna("").astype(str).str.strip().tolist() if c])
    if "tags" in df.columns:
        for cell in df["tags"].fillna("").astype(str):
            words.extend(_parse_tokens(cell))
    vocab = [w for w in words if 2 <= len(w) <= 40]
    counts = Counter([w.lower() for w in vocab])
    return [w for w, _ in counts.most_common()]


@st.cache_data(show_spinner=False)
def load_data() -> Tuple[pd.DataFrame, str, List[str]]:
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

    # Stable ID per row for favorites/usage
    def _rid(q, a):
        return hashlib.md5((q + '||' + a).encode('utf-8')).hexdigest()[:16]
    df["rid"] = [_rid(q, a) for q, a in zip(df["question"], df["answer"])]

    df = df[(df["question"] != "") & (df["answer"] != "")].reset_index(drop=True)
    topics = _extract_topic_vocab(df)
    return df, csv_path.name, topics


@st.cache_data(show_spinner=False)
def load_brokerage_table() -> Tuple[pd.DataFrame, str]:
    """Load brokerage rebuttals from Excel (all sheets)."""
    base = Path(__file__).parent
    x_path = None
    for name in BROKERAGE_FILES:
        p = base / name
        if p.exists():
            x_path = p
            break
    if x_path is None:
        raise FileNotFoundError(f"To use Brokerage Compare, place one of these files next to the app: {', '.join(BROKERAGE_FILES)}")

    # Read all sheets
    xl = pd.ExcelFile(x_path)
    frames = []
    for s in xl.sheet_names:
        try:
            frames.append(xl.parse(s))
        except Exception:
            continue
    if not frames:
        raise ValueError(f"No readable sheets found in '{x_path.name}'.")
    raw = pd.concat(frames, ignore_index=True)
    raw = raw.dropna(axis=1, how="all")
    if raw.empty:
        raise ValueError(f"'{x_path.name}' is empty.")

    # Map columns
    def pick(colnames, keys):
        cols_l = [str(c).strip().lower() for c in colnames]
        for k in keys:
            k = str(k).strip().lower()
            if k in cols_l:
                return colnames[cols_l.index(k)]
        for k in keys:
            k = str(k).strip().lower()
            for i,c in enumerate(cols_l):
                if k in c:
                    return colnames[i]
        return None

    b_col = pick(list(raw.columns), ["brokerage","broker","company","brand","target_brokerage"])
    r_col = pick(list(raw.columns), ["rebuttal","answer","response","script","talk_track","talking_points"])
    s_col = pick(list(raw.columns), ["sms","sms_copy","text","text_message"])
    o_col = pick(list(raw.columns), ["one_liner","one-liner","oneliner","soundbite","hook"])
    n_col = pick(list(raw.columns), ["notes","context","angle","why_this_works"])

    if b_col is None or r_col is None:
        raise KeyError("Brokerage file must include Brokerage and Rebuttal columns.")

    df = pd.DataFrame({
        "brokerage": raw[b_col].astype(str).str.strip(),
        "rebuttal": raw[r_col].astype(str).str.strip(),
        "sms": raw[s_col].fillna("").astype(str).str.strip() if s_col else "",
        "one_liner": raw[o_col].fillna("").astype(str).str.strip() if o_col else "",
        "notes": raw[n_col].fillna("").astype(str).str.strip() if n_col else "",
    }).dropna(how="all")

    # Filter blanks
    df = df[df["brokerage"] != ""]
    # Stable ID for compare
    df["bid"] = [hashlib.md5((b + '||' + r).encode('utf-8')).hexdigest()[:12] for b, r in zip(df["brokerage"], df["rebuttal"])]
    # Sort by brokerage name
    df = df.sort_values("brokerage").reset_index(drop=True)
    return df, x_path.name


def copy_button(label: str, text: str, key: str):
    """Small JS copy-to-clipboard button without external packages."""
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
    """Browser TTS play/stop without external services."""
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
        const makeU = () => {{ const u = new SpeechSynthesisUtterance(txt); u.rate = rate; u.pitch = pitch; return u; }};
        document.getElementById("{key}-play").onclick = () => {{ try {{ speechSynthesis.cancel(); speechSynthesis.speak(makeU()); }} catch(e){{}} }};
        document.getElementById("{key}-stop").onclick = () => {{ try {{ speechSynthesis.cancel(); }} catch(e){{}} }};
      }})();
    </script>
    """
    components.html(html, height=50)


def apply_filters(frame: pd.DataFrame,
                  term: str = "",
                  selected_topics: List[str] | None = None,
                  match_mode: str = "Any",
                  category: str | None = None,
                  tag: str | None = None) -> pd.DataFrame:
    out = frame

    if term and term.strip():
        tl = term.strip().lower()
        out = out[out["question"].str.lower().str.contains(tl)]

    if selected_topics:
        targets = [t.lower() for t in selected_topics]

        def has_topics(row):
            bag = set()
            if isinstance(row.get("category", ""), str) and row["category"].strip():
                bag.add(row["category"].strip().lower())
            if isinstance(row.get("tags", ""), str) and row["tags"].strip():
                bag.update([t.lower() for t in _parse_tokens(row["tags"])])
            return all(t in bag for t in targets) if match_mode == "All" else any(t in bag for t in targets)

        out = out[out.apply(has_topics, axis=1)]

    if category and category != "All":
        out = out[out["category"] == category]

    if tag and tag != "All":
        def has_tag(cell: str) -> bool:
            cell = (cell or "").lower().replace("|", ",").replace(";", ",")
            toks = [t.strip() for t in cell.split(",") if t.strip()]
            return tag.lower() in toks
        out = out[out["tags"].apply(has_tag)]

    return out


def objections_ui():
    # Session state
    if "favorites" not in st.session_state:
        st.session_state.favorites = {}   # rid -> row dict
    if "view_counts" not in st.session_state:
        st.session_state.view_counts = {} # rid -> int

    # Load primary dataset
    try:
        df, used_file, topics = load_data()
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        return

    # Sidebar
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
    tag_tokens = sorted({t for v in df["tags"].fillna('').astype(str) for t in _parse_tokens(v)})
    category = st.sidebar.selectbox("Category", ["All"] + cats, index=0) if cats else None
    tag = st.sidebar.selectbox("Tag", ["All"] + tag_tokens, index=0) if tag_tokens else None

    st.sidebar.markdown("---")
    st.sidebar.markdown("### My Deck")
    st.sidebar.write(f"⭐ Favorites: **{len(st.session_state.favorites)}**")
    if st.session_state.favorites:
        fav_df = pd.DataFrame(st.session_state.favorites.values())
        st.sidebar.download_button("⬇️ Download Deck (CSV)", fav_df.to_csv(index=False).encode("utf-8"),
                           file_name="my_deck.csv", mime="text/csv")
    up = st.sidebar.file_uploader("⬆️ Upload Deck CSV", type=["csv"], label_visibility="collapsed")
    if up is not None:
        try:
            up_df = pd.read_csv(up)
            q_col = [c for c in up_df.columns if c.lower() == "question"]
            a_col = [c for c in up_df.columns if c.lower() == "answer"]
            if q_col and a_col:
                q_col = q_col[0]; a_col = a_col[0]
                c_col = [c for c in up_df.columns if c.lower() == "category"]
                t_col = [c for c in up_df.columns if c.lower() == "tags"]
                for _, r in up_df.iterrows():
                    q = str(r[q_col]).strip(); a = str(r[a_col]).strip()
                    if not q or not a: continue
                    rid = hashlib.md5((q + "||" + a).encode("utf-8")).hexdigest()[:16]
                    st.session_state.favorites[rid] = {
                        "rid": rid, "question": q, "answer": a,
                        "category": str(r[c_col[0]]).strip() if c_col else "",
                        "tags": str(r[t_col[0]]).strip() if t_col else "",
                    }
                st.sidebar.success("Deck merged into favorites.")
            else:
                st.sidebar.warning("CSV must have at least: question, answer")
        except Exception as e:
            st.sidebar.error(f"Upload failed: {e}")

    st.sidebar.markdown("---")
    rate = st.sidebar.slider("Voice speed", 0.6, 1.4, 1.0, 0.05)
    pitch = st.sidebar.slider("Voice pitch", 0.5, 1.5, 1.0, 0.05)
    st.session_state['tts_rate'] = rate
    st.session_state['tts_pitch'] = pitch

    # Views
    view = st.radio("View", ["All", "Favorites", "Most Used"], horizontal=True)
    if view == "Favorites":
        fav_ids = set(st.session_state.favorites.keys())
        filt = df[df["rid"].isin(fav_ids)]
    elif view == "Most Used":
        counts = st.session_state.view_counts
        ordered_ids = sorted(counts.keys(), key=lambda k: counts[k], reverse=True)[:50]
        filt = df[df["rid"].isin(ordered_ids)]
        filt = filt.sort_values(by="rid", key=lambda s: s.map(lambda rid: counts.get(rid, 0)), ascending=False)
    else:
        filt = df

    # Apply filters
    filt = apply_filters(filt, term, selected_topics, match_mode, category, tag)

    st.write(f"Matches: **{len(filt)}**")
    if filt.empty:
        st.warning("No results. Try clearing filters or a different view.")
        return

    options = [f"{i}. {q[:120]}" for i, q in enumerate(filt['question'].tolist())]
    selected = st.selectbox("Pick an objection", options, index=0, label_visibility="collapsed")
    sel_idx = int(selected.split(". ", 1)[0])
    row = filt.iloc[sel_idx]

    rid = row["rid"]
    st.session_state.view_counts[rid] = st.session_state.view_counts.get(rid, 0) + 1

    st.subheader("Objection")
    if row["category"]:
        st.write(f"**Category:** {row['category']}")
    st.write(row["question"])

    st.subheader("Rebuttal")
    st.markdown(row["answer"])

    st.markdown("---")
    cols = st.columns([1,1,1,3])
    with cols[0]:
        is_fav = rid in st.session_state.favorites
        if not is_fav:
            if st.button("⭐ Add to Favorites"):
                st.session_state.favorites[rid] = {
                    "rid": rid,
                    "question": row["question"],
                    "answer": row["answer"],
                    "category": row.get("category",""),
                    "tags": row.get("tags",""),
                }
                st.rerun()
        else:
            if st.button("★ Remove Favorite"):
                st.session_state.favorites.pop(rid, None)
                st.rerun()

    with cols[1]:
        copy_button("Copy Rebuttal", row["answer"], key=f"copy-rebuttal-{rid}")

    with cols[2]:
        st.download_button("Download Rebuttal.txt", data=row["answer"].encode("utf-8"),
                           file_name="rebuttal.txt", mime="text/plain")

    st.markdown("---")
    st.subheader("Listen")
    st.caption("Uses your browser's built‑in voice (no upload).")
    tts_controls(row["answer"], rate=rate, pitch=pitch, key="tts1")

    with st.expander("⭐ Favorites & 🔥 Most Used (this session)"):
        fav_count = len(st.session_state.favorites)
        st.write(f"Favorites: **{fav_count}**")
        if fav_count:
            fdf = pd.DataFrame(st.session_state.favorites.values())
            st.dataframe(fdf[["question","category","tags"]].rename(columns={"question":"Objection"}),
                         use_container_width=True, height=240)
        if st.session_state.view_counts:
            top = sorted(st.session_state.view_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
            top_rows = df[df["rid"].isin([rid for rid,_ in top])].copy()
            top_rows["views"] = top_rows["rid"].map(dict(top))
            st.write("Most Used:")
            st.dataframe(top_rows[["question","views","category","tags"]].rename(columns={"question":"Objection"}),
                         use_container_width=True, height=240)


def brokerage_ui():
    st.subheader("Brokerage Compare")
    try:
        bdf, used_file = load_brokerage_table()
    except Exception as e:
        st.info(f"Brokerage dataset not found or invalid: {e}")
        st.caption("Drop the Excel next to the app and rerun to enable this tab.")
        return

    st.caption(f"Using: `{used_file}`")

    brokerages = sorted(bdf["brokerage"].unique().tolist())
    left, right = st.columns([2,3])
    with left:
        search = st.text_input("Search brokerages", "")
        options = [b for b in brokerages if search.lower() in b.lower()] if search.strip() else brokerages
        picked = st.selectbox("Pick a brokerage", options, index=0 if options else 0)

        compare_fp = st.checkbox("Compare to Funnel Pilot", value=False)
    with right:
        pass

    if not picked:
        st.warning("Select a brokerage to view content.")
        return

    main_row = bdf[bdf["brokerage"] == picked].iloc[0]

    # Primary view
    st.markdown("### Primary")
    st.write(f"**Brokerage:** {picked}")
    st.markdown("**Rebuttal**")
    st.markdown(main_row["rebuttal"] or "_(none)_")
    st.markdown("**One‑liner**")
    st.write(main_row["one_liner"] or "_(none)_")
    st.markdown("**SMS**")
    st.code(main_row["sms"] or "(none)", language="text")
    if main_row["notes"]:
        st.markdown("> " + main_row["notes"])


    st.markdown("---")
    st.markdown("**Listen**")
    _rate = st.session_state.get("tts_rate", 1.0)
    _pitch = st.session_state.get("tts_pitch", 1.0)
    tts_controls(main_row.get("rebuttal", ""), rate=_rate, pitch=_pitch, key=f"tts-b-{main_row['bid']}")

    # Actions
    st.markdown("**Quick actions**")
    ac = st.columns(3)
    with ac[0]:
        copy_button("Copy Rebuttal", main_row["rebuttal"], key=f"copy-breb-{main_row['bid']}")
    with ac[1]:
        copy_button("Copy SMS", main_row["sms"], key=f"copy-bsms-{main_row['bid']}")
    with ac[2]:
        copy_button("Copy One‑liner", main_row["one_liner"], key=f"copy-bone-{main_row['bid']}")

    
    # Build a single text blob safely (avoid nested f-string quoting issues)
    rebuttal_txt = str(main_row.get("rebuttal", ""))
    one_liner_txt = str(main_row.get("one_liner", ""))
    sms_txt = str(main_row.get("sms", ""))
    pack_text = "Brokerage: {0}\n\nRebuttal:\n{1}\n\nOne-liner:\n{2}\n\nSMS:\n{3}\n".format(
        picked, rebuttal_txt, one_liner_txt, sms_txt
    )

    st.download_button(
        "Download All (TXT)",
        data=pack_text.encode("utf-8"),
        file_name=f"{picked.replace(' ', '_')}_pack.txt",
        mime="text/plain",
    )

    
    # Compare (optional) — Funnel Pilot only
    if compare_fp:
        st.markdown("---")
        st.markdown("### Compare to Funnel Pilot")
        fp = bdf[bdf["brokerage"].str.lower().str.contains("funnel pilot")]
        if fp.empty:
            st.info("No 'Funnel Pilot' row found in the workbook. Add one to enable this comparison.")
        else:
            fp_row = fp.iloc[0]
            colA, colB = st.columns(2)
            with colA:
                st.markdown("**Your Pick**")
                st.write(f"**Brokerage:** {picked}")
                st.markdown("**One‑liner**")
                st.write(main_row.get("one_liner", "") or "_(none)_")
                st.markdown("**Rebuttal**")
                st.markdown(main_row.get("rebuttal", "") or "_(none)_")
                st.markdown("**SMS**")
                st.code(main_row.get("sms", "") or "(none)", language="text")
            with colB:
                st.markdown("**Funnel Pilot**")
                st.markdown("**One‑liner**")
                st.write(fp_row.get("one_liner", "") or "_(none)_")
                st.markdown("**Rebuttal**")
                st.markdown(fp_row.get("rebuttal", "") or "_(none)_")
                st.markdown("**SMS**")
                st.code(fp_row.get("sms", "") or "(none)", language="text")

            # Positioning script (crafted)
            st.markdown("#### Positioning Script")
script_lines = [
    f"Totally hear the appeal of {picked}. Here’s why agents who compare it to Funnel Pilot usually choose FP:",
    "",
    "• Control & ownership: your ads, your CRM, your data — you keep everything if you move.",
    "• Lower lead cost & testing speed: FP iterates creatives/targets fast to keep CPL in the $3–$5 band.",
    "• Done‑for‑you buildout: domains, A2P, automations, lender co‑marketing — it’s set up end‑to‑end.",
    "• Weekly coaching + scripts: practice the exact talk tracks that convert and get real‑time tweaks.",
    "• Aligned incentives: no platform fee — FP only wins when you close.",
    "",
    "Given that, would it be crazy to run the first 60–90 days with FP, see the ROI, and then decide from a position of data?",
]
script = "
".join(script_lines)
st.write(script)
copy_button("Copy Positioning Script", script, key=f"copy-fp-script-{main_row['bid']}")


def main():
    st.set_page_config(page_title="Pocket Objections — Simple", layout="wide")
    st.title("Pocket Objections — Simple")
    tab1, tab2 = st.tabs(["🎯 Objections", "🏢 Brokerage Compare"])
    with tab1:
        objections_ui()
    with tab2:
        brokerage_ui()
    st.caption("Empathy → short frame → value → tie‑down → next step.")


if __name__ == "__main__":
    main()
