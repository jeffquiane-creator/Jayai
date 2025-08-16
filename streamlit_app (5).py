
import random
from pathlib import Path
import pandas as pd
import streamlit as st

# ------------- Config -------------
CANDIDATE_DATASETS = [
    "Agent_Objection_Rebuttals_Dataset_Categorized - Agent_Objection_Rebuttals_Dataset_Categorized.csv.csv",  # exact uploaded name
    "Agent_Objection_Rebuttals_Dataset_Categorized.csv",
    "training_dataset.csv",
]

REQUIRED_COLS = ("filename", "question", "category", "answer")

HEADER_ALIASES = {
    "filename": ["filename", "file", "source", "doc", "transcript"],
    "question": ["question", "objection", "prompt", "q", "objection_text", "question_text"],
    "category": ["category", "cat", "topic", "bucket", "group"],
    "answer":   ["answer", "response", "reply", "rebuttal", "a", "jay_style_answer"],
}

def _find_col(cols_lower, want):
    aliases = HEADER_ALIASES[want]
    for name in aliases:
        if name in cols_lower:
            return name
    return None

@st.cache_data(show_spinner=False)
def load_dataset_auto(drop_dupes: bool) -> tuple[pd.DataFrame, str, list]:
    """Load dataset from candidate filenames, normalize headers, clean rows, and optionally de-duplicate."""
    base = Path(__file__).parent
    csv_path = None
    for name in CANDIDATE_DATASETS:
        p = base / name
        if p.exists():
            csv_path = p
            break
    if csv_path is None:
        raise FileNotFoundError(f"Could not find a dataset. Expected one of: {', '.join(CANDIDATE_DATASETS)}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"Dataset '{csv_path.name}' is empty.")

    original_cols = list(df.columns)
    df.columns = [str(c).strip().lower() for c in df.columns]

    colmap = {k: _find_col(df.columns, k) for k in HEADER_ALIASES.keys()}

    out = pd.DataFrame()
    # filename
    out["filename"] = (
        df[colmap["filename"]].astype(str).str.strip()
        if colmap["filename"] is not None
        else "jay_objections_master"
    )
    out.loc[out["filename"] == "", "filename"] = "jay_objections_master"

    # question
    if colmap["question"] is None:
        raise KeyError("Dataset must have a question/objection column (e.g., 'question' or 'objection').")
    out["question"] = df[colmap["question"]].astype(str).str.strip()

    # category
    out["category"] = (
        df[colmap["category"]].astype(str).str.strip()
        if colmap["category"] is not None
        else "objections/uncategorized"
    )
    out.loc[out["category"] == "", "category"] = "objections/uncategorized"

    # answer
    if colmap["answer"] is None:
        raise KeyError("Dataset must have a response/answer column (e.g., 'answer', 'response', or 'rebuttal').")
    out["answer"] = df[colmap["answer"]].astype(str).str.strip()

    # Clean
    out = out.dropna(subset=["question", "answer"])
    out = out[(out["question"] != "") & (out["answer"] != "")]

    before = len(out)
    if drop_dupes:
        q_norm = out["question"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
        out = out.loc[q_norm.drop_duplicates().index]
    out = out.reset_index(drop=True)

    return out, csv_path.name, original_cols, before

def pick_random_row(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        raise ValueError("No data loaded from the dataset after cleaning.")
    idx = random.randrange(len(df))
    return df.iloc[idx]

def main():
    st.set_page_config(page_title="Jay-Style Objection Rebuttal Practice")
    st.title("Jay-Style Objection Rebuttal Practice")

    # Controls
    with st.sidebar:
        st.markdown("### Dataset settings")
        drop_dupes = st.checkbox("Remove duplicate questions", value=False, help="Uncheck to keep all rows in the dataset.")

    # Load
    try:
        df, used_file, original_cols, before_count = load_dataset_auto(drop_dupes=drop_dupes)
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        st.info(f"Place one of these files next to this app: {', '.join(CANDIDATE_DATASETS)}")
        return

    with st.sidebar:
        st.write(f"**Loaded file:** `{used_file}`")
        st.write(f"**Rows (after cleaning):** {len(df)} (from {before_count})")
        st.write("**Detected columns:**")
        st.code(", ".join(original_cols), language="text")

        cats = sorted(df["category"].dropna().unique().tolist())
        selected = st.multiselect("Filter by category", cats, default=[])
        query = st.text_input("Search (question contains)", "")

    # Apply filters
    filt = df
    if selected:
        filt = filt[filt["category"].isin(selected)]
    if query.strip():
        ql = query.strip().lower()
        filt = filt[filt["question"].str.lower().str.contains(ql)]

    st.write(f"Questions available after filters: **{len(filt)}**")
    if len(filt) == 0:
        st.warning("No rows match the current filters. Clear filters or adjust your search.")
        return

    # UI
    if "current_idx" not in st.session_state:
        st.session_state.current_idx = None

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎲 Random objection"):
            st.session_state.current_idx = random.randrange(len(filt))
    with c2:
        if st.button("⟲ Reset selection"):
            st.session_state.current_idx = None

    row = filt.iloc[random.randrange(len(filt))] if st.session_state.current_idx is None else filt.iloc[st.session_state.current_idx]

    st.subheader("Objection")
    st.write(f"**Category:** {row['category']}")
    st.write(row["question"])

    st.subheader("Your response")
    st.text_area("Type your rebuttal (or talk it out loud while you type notes):", height=140, key="user_resp")

    with st.expander("Show suggested rebuttal (Jay-style + classic sales principles)"):
        st.markdown(row["answer"])

    st.caption("Tip: Empathize → frame value → tiny tie-down → ask for the next step.")

if __name__ == "__main__":
    main()
