
import random
from pathlib import Path
import pandas as pd
import streamlit as st

# ---------------- Config ----------------
CANDIDATE_DATASETS = [
    "100_Unique_Objections___Rebuttals - 100_Unique_Objections___Rebuttals.csv (3).csv",  # your latest file
    "100_Unique_Objections___Rebuttals.csv",
    "Objection_Rebuttal_Master_500 (1).csv",
    "Objection_Rebuttal_Master_500.csv",
    "Agent_Objection_Rebuttals_Dataset_Categorized.csv",
    "training_dataset.csv",
]

HEADER_ALIASES = {
    # Support slash headers and common variants
    "question": ["objection/question", "objection", "question", "prompt", "q"],
    "answer":   ["rebuttal/answer", "rebuttal", "answer", "response", "reply"],
    "category": ["category", "topic", "bucket"],
    "tags":     ["tags", "keywords", "labels"],
}

def _lowerstrip(s): 
    return str(s).strip().lower()

def _find_col(cols, targets):
    cols_l = [_lowerstrip(c) for c in cols]
    # exact match first
    for t in targets:
        t_l = _lowerstrip(t)
        if t_l in cols_l:
            return cols[cols_l.index(t_l)]
    # soft contains match (handles e.g. "Objection/Question")
    for t in targets:
        t_l = _lowerstrip(t)
        for i, c in enumerate(cols_l):
            if t_l in c:
                return cols[i]
    return None

def _parse_tags(series: pd.Series):
    # Split tags on |, ;, or , and strip
    tokens = []
    for v in series.fillna("").astype(str):
        if not v.strip():
            continue
        # normalize separators
        tmp = v.replace("|", ",").replace(";", ",")
        for t in tmp.split(","):
            t = t.strip()
            if t:
                tokens.append(t)
    return sorted(set(tokens))

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
    raw = raw.dropna(axis=1, how="all")  # drop fully empty columns
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
    if c_col:
        df["category"] = raw[c_col].fillna("").astype(str).str.strip()
    else:
        df["category"] = ""

    if t_col:
        df["tags"] = raw[t_col].fillna("").astype(str).str.strip()
    else:
        df["tags"] = ""

    # Clean minimal
    df = df[(df["question"] != "") & (df["answer"] != "")].reset_index(drop=True)
    return df, csv_path.name

def main():
    st.set_page_config(page_title="Pocket Objections (Simple)", layout="centered")
    st.title("Pocket Objections — Simple")
    st.caption("Search • Filter • Read the rebuttal. No clutter.")

    # Load
    try:
        df, used_file = load_data()
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        return

    # --- Sidebar: simple filters ---
    with st.sidebar:
        st.markdown("### Filters")
        st.write(f"Using: `{used_file}`")
        term = st.text_input("Search in objection", "")

        # Category filter (only if present)
        cats = sorted([c for c in df["category"].unique().tolist() if c])
        category = None
        if len(cats) > 0:
            category = st.selectbox("Category", ["All"] + cats, index=0)

        # Tag filter (only if present)
        tag_tokens = _parse_tags(df["tags"]) if "tags" in df.columns else []
        tag = None
        if len(tag_tokens) > 0:
            tag = st.selectbox("Tag", ["All"] + tag_tokens, index=0)

    # --- Apply filters ---
    filt = df
    if term.strip():
        tl = term.strip().lower()
        filt = filt[filt["question"].str.lower().str.contains(tl)]
    if category and category != "All":
        filt = filt[filt["category"] == category]
    if tag and tag != "All":
        # case-insensitive token match within tags cell
        filt = filt[filt["tags"].str.lower().str.split(r"[|;,]", expand=False).apply(lambda xs: any(t.strip()==tag.lower() for t in xs if isinstance(xs, list)))]
    count = len(filt)

    st.write(f"Matches: **{count}**")
    if count == 0:
        st.warning("No results. Try clearing filters or a different search.")
        return

    # --- Selection ---
    # small selectbox of the current filtered objections
    options = [f"{i}. {q[:120]}" for i, q in enumerate(filt['question'].tolist())]
    selected = st.selectbox("Pick an objection", options, index=0, label_visibility="collapsed")
    sel_idx = int(selected.split(". ", 1)[0])
    row = filt.iloc[sel_idx]

    # --- Display ---
    st.subheader("Objection")
    if row["category"]:
        st.write(f"**Category:** {row['category']}")
    st.write(row["question"])

    st.subheader("Rebuttal")
    st.markdown(row["answer"])

    # Optional tag chips
    if "tags" in df.columns and isinstance(row.get("tags",""), str) and row.get("tags","").strip():
        st.caption("Tags: " + ", ".join([t.strip() for t in row["tags"].replace("|",";").split(";") if t.strip()]))

    st.caption("Empathy → short frame → value → tie‑down → next step.")

if __name__ == "__main__":
    main()
