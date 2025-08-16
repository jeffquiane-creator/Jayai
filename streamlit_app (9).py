
import random
from pathlib import Path
import pandas as pd
import streamlit as st

# ---------------- Config ----------------
CANDIDATE_DATASETS = [
    # New uploaded file first
    "100_Unique_Objections___Rebuttals - 100_Unique_Objections___Rebuttals.csv (3).csv",
    # Common alternates / renames
    "100_Unique_Objections___Rebuttals.csv",
    "Objection_Rebuttal_Master_500 (1).csv",
    "Objection_Rebuttal_Master_500.csv",
    "Agent_Objection_Rebuttals_Dataset_Categorized.csv",
    "training_dataset.csv",
]

HEADER_ALIASES = {
    # Include slash-style headers from the new file
    "question": ["objection/question", "objection", "question", "prompt", "q"],
    "answer":   ["rebuttal/answer", "rebuttal", "answer", "response", "reply"],
    "category": ["category", "topic", "bucket"],
    "tags":     ["tags", "keywords", "labels"],
}

def _lowerstrip(s): 
    return str(s).strip().lower()

def _find_col(cols, targets):
    cols_l = [_lowerstrip(c) for c in cols]
    # direct match first
    for t in targets:
        t_l = _lowerstrip(t)
        if t_l in cols_l:
            return cols[cols_l.index(t_l)]
    # fallback: soft match if a column CONTAINS the token (e.g., "objection/question")
    for t in targets:
        t_l = _lowerstrip(t)
        for i, c in enumerate(cols_l):
            if t_l in c:
                return cols[i]
    return None

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

    # Read CSV and drop fully empty columns
    raw = pd.read_csv(csv_path)
    raw = raw.dropna(axis=1, how="all")
    if raw.empty:
        raise ValueError(f"Dataset '{csv_path.name}' is empty.")

    # map columns
    q_col = _find_col(list(raw.columns), HEADER_ALIASES["question"])
    a_col = _find_col(list(raw.columns), HEADER_ALIASES["answer"])
    c_col = _find_col(list(raw.columns), HEADER_ALIASES["category"])
    t_col = _find_col(list(raw.columns), HEADER_ALIASES["tags"])

    if q_col is None or a_col is None:
        raise KeyError("Dataset needs columns for objection/question and rebuttal/answer.")

    df = pd.DataFrame({
        "question": raw[q_col].astype(str).str.strip(),
        "answer":   raw[a_col].astype(str).str.strip(),
        "category": raw[c_col].astype(str).str.strip() if c_col else "uncategorized",
        "tags":     raw[t_col].astype(str).str.strip() if t_col else "",
    })

    # Clean: drop empty rows
    df = df[(df["question"] != "") & (df["answer"] != "")].reset_index(drop=True)
    return df, csv_path.name, list(raw.columns)

def main():
    st.set_page_config(page_title="Jay-Style Pocket Objections (Simple)", layout="centered")
    st.title("Jay‑Style Pocket Objections")
    st.caption("Search • Randomize • Get a clean talk track.")

    # Load
    try:
        df, used_file, raw_cols = load_data()
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        return

    # Sidebar (minimal)
    with st.sidebar:
        st.markdown("### Dataset")
        st.write(f"**Loaded file:** `{used_file}`")
        st.write(f"**Rows:** {len(df)}")
        st.write("**Columns detected:**")
        st.code(", ".join([str(c) for c in raw_cols]), language="text")

        # Filters
        cats = sorted(df["category"].dropna().unique().tolist())
        category = st.selectbox("Category (optional)", ["All"] + cats, index=0)
        query = st.text_input("Search (in objection)", "")

    # Apply filters
    filt = df
    if category != "All":
        filt = filt[filt["category"] == category]
    if query.strip():
        ql = query.strip().lower()
        filt = filt[filt["question"].str.lower().str.contains(ql)]

    st.write(f"Matches: **{len(filt)}**")
    if len(filt) == 0:
        st.warning("No matches. Clear filters or try a different term.")
        return

    # Selection controls
    col1, col2 = st.columns(2)
    if "idx" not in st.session_state:
        st.session_state.idx = 0

    with col1:
        if st.button("🎲 Random"):
            st.session_state.idx = random.randrange(len(filt))
    with col2:
        st.session_state.idx = st.number_input("Row #", min_value=0, max_value=max(len(filt)-1, 0), value=st.session_state.idx, step=1)

    row = filt.iloc[st.session_state.idx]

    # Display
    st.subheader("Objection")
    st.write(f"**Category:** {row['category']}")
    st.write(row["question"])

    st.subheader("Suggested rebuttal")
    st.markdown(row["answer"])

    st.caption("Keep it simple: empathy → short frame → value → tie‑down → next step.")

if __name__ == "__main__":
    main()
