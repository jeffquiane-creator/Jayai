
import random
import hashlib
from pathlib import Path
import json
import re
import io
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
    counts = Counter([w.lower() for w in vocab])
    return [w for w, _ in counts.most_common()]

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

    # Stable ID per row for favorites/usage (md5 of question+answer)
    def _rid(q, a):
        h = hashlib.md5((q + "||" + a).encode("utf-8")).hexdigest()
        return h[:16]
    df["rid"] = [ _rid(q, a) for q,a in zip(df["question"], df["answer"]) ]

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

def main():
    st.set_page_config(page_title="Pocket Objections (Simple)", layout="centered")
    st.title("Pocket Objections — Simple")
    st.caption("Save ⭐ favorites, see Most Used, and grab rebuttals fast.")

    # Global state
    if "favorites" not in st.session_state:
        st.session_state.favorites = {}   # rid -> row dict
    if "view_counts" not in st.session_state:
        st.session_state.view_counts = {} # rid -> int

    try:
        df, used_file, topics = load_data()
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        return

    # ---- Sidebar: Filters + Deck tools ----
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
        st.markdown("### My Deck")
        st.write(f"⭐ Favorites: **{len(st.session_state.favorites)}**")
        # Download deck
        if st.session_state.favorites:
            import pandas as pd
            fav_df = pd.DataFrame(st.session_state.favorites.values())
            st.download_button("⬇️ Download Deck (CSV)", fav_df.to_csv(index=False).encode("utf-8"),
                               file_name="my_deck.csv", mime="text/csv")
        # Upload deck
        up = st.file_uploader("⬆️ Upload Deck CSV", type=["csv"], label_visibility="collapsed")
        if up is not None:
            try:
                up_df = pd.read_csv(up)
                required = {"question","answer"}
                if not required.issubset(set([c.lower() for c in up_df.columns])):
                    st.warning("CSV must have at least columns: question, answer")
                else:
                    q_col = [c for c in up_df.columns if c.lower()=="question"][0]
                    a_col = [c for c in up_df.columns if c.lower()=="answer"][0]
                    c_col = [c for c in up_df.columns if c.lower()=="category"]
                    t_col = [c for c in up_df.columns if c.lower()=="tags"]
                    for _, r in up_df.iterrows():
                        q = str(r[q_col]).strip()
                        a = str(r[a_col]).strip()
                        if not q or not a: 
                            continue
                        rid = hashlib.md5((q + "||" + a).encode("utf-8")).hexdigest()[:16]
                        st.session_state.favorites[rid] = {
                            "rid": rid,
                            "question": q,
                            "answer": a,
                            "category": str(r[c_col[0]]).strip() if c_col else "",
                            "tags": str(r[t_col[0]]).strip() if t_col else "",
                        }
                    st.success("Deck merged into favorites.")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    # ---- View mode ----
    view = st.radio("View", ["All", "Favorites", "Most Used"], horizontal=True)
    filt = df

    # Apply filters common to all
    def apply_filters(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame
        if term.strip():
            tl = term.strip().lower()
            out = out[out["question"].str.lower().str.contains(tl)]
        if selected_topics:
            def has_topics(row):
                bag = set()
                if isinstance(row.get("category",""), str) and row["category"].strip():
                    bag.add(row["category"].strip().lower())
                if isinstance(row.get("tags",""), str) and row["tags"].strip():
                    bag.update([t.lower() for t in _parse_tokens(row["tags"])])
                targets = [t.lower() for t in selected_topics]
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

    if view == "Favorites":
        fav_ids = set(st.session_state.favorites.keys())
        filt = df[df["rid"].isin(fav_ids)]
        filt = apply_filters(filt)
    elif view == "Most Used":
        # take top 50 by view count, then apply filters
        counts = st.session_state.view_counts
        ordered_ids = sorted(counts.keys(), key=lambda k: counts[k], reverse=True)[:50]
        filt = df[df["rid"].isin(ordered_ids)]
        filt = apply_filters(filt)
        # sort by usage desc for display
        filt = filt.sort_values(by="rid", key=lambda s: s.map(lambda rid: counts.get(rid, 0)), ascending=False)
    else:
        # All
        filt = apply_filters(df)

    count = len(filt)
    st.write(f"Matches: **{count}**")
    if count == 0:
        st.warning("No results. Try clearing filters or a different view.")
        return

    options = [f"{i}. {q[:120]}" for i, q in enumerate(filt['question'].tolist())]
    # default selection: keep previous index if possible
    default_idx = 0
    selected = st.selectbox("Pick an objection", options, index=default_idx, label_visibility="collapsed")
    sel_idx = int(selected.split(". ", 1)[0])
    row = filt.iloc[sel_idx]

    # increment usage
    rid = row["rid"]
    st.session_state.view_counts[rid] = st.session_state.view_counts.get(rid, 0) + 1

    # ----- Display -----
    st.subheader("Objection")
    if row["category"]:
        st.write(f"**Category:** {row['category']}")
    st.write(row["question"])

    st.subheader("Rebuttal")
    st.markdown(row["answer"])

    # Favorite toggle + quick actions
    st.markdown("---")
    cols = st.columns([1,1,1,4])
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
                st.experimental_rerun()
        else:
            if st.button("★ Remove Favorite"):
                st.session_state.favorites.pop(rid, None)
                st.experimental_rerun()

    with cols[1]:
        # Copy rebuttal
        safe_id = f"copy-rebuttal-{rid}"
        copy_button("Copy Rebuttal", row["answer"], key=safe_id)

    with cols[2]:
        # Download rebuttal
        st.download_button("Download Rebuttal.txt", data=row["answer"].encode("utf-8"),
                           file_name="rebuttal.txt", mime="text/plain")

    # Surface Most Used / Favorites summaries
    with st.expander("⭐ Favorites & 🔥 Most Used (this session)"):
        fav_count = len(st.session_state.favorites)
        st.write(f"Favorites: **{fav_count}**")
        if fav_count:
            fdf = pd.DataFrame(st.session_state.favorites.values())
            st.dataframe(fdf[["question","category","tags"]].rename(columns={"question":"Objection"}), use_container_width=True, height=240)
        if st.session_state.view_counts:
            top = sorted(st.session_state.view_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
            top_rows = df[df["rid"].isin([rid for rid,_ in top])].copy()
            top_rows["views"] = top_rows["rid"].map(dict(top))
            st.write("Most Used:")
            st.dataframe(top_rows[["question","views","category","tags"]].rename(columns={"question":"Objection"}),
                         use_container_width=True, height=240)

    st.caption("Empathy → short frame → value → tie‑down → next step.")

if __name__ == "__main__":
    main()
