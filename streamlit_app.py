
import random
from pathlib import Path
import pandas as pd
import streamlit as st

# ------------- Config -------------
CANDIDATE_DATASETS = [
    "Agent_Objection_Rebuttals_Dataset_Categorized.csv",  # new dataset name
    "training_dataset.csv",                               # fallback
]

REQUIRED_COLS = ("filename", "question", "category", "answer")

# Allow common header variations -> normalize to REQUIRED_COLS
HEADER_ALIASES = {
    "filename": ["filename", "file", "source", "doc", "transcript"],
    "question": ["question", "objection", "prompt", "q", "objection_text"],
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
def load_dataset_auto() -> pd.DataFrame:
    """Load dataset from any of the candidate filenames, normalize headers, and clean rows."""
    base = Path(__file__).parent
    csv_path = None
    for name in CANDIDATE_DATASETS:
        p = base / name
        if p.exists():
            csv_path = p
            break

    if csv_path is None:
        raise FileNotFoundError(
            "Could not find a dataset next to the app. "
            f"Expected one of: {', '.join(CANDIDATE_DATASETS)}"
        )

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"Dataset '{csv_path.name}' is empty.")

    # Normalize headers
    original_cols = list(df.columns)
    df.columns = [str(c).strip().lower() for c in df.columns]

    colmap = {}
    for req in REQUIRED_COLS:
        found = _find_col(df.columns, req)
        colmap[req] = found

    # Build the normalized frame with safe defaults
    out = pd.DataFrame()
    # filename
    if colmap["filename"] is not None:
        out["filename"] = df[colmap["filename"]].astype(str).str.strip().replace({"": "jay_objections_master"})
    else:
        out["filename"] = "jay_objections_master"
    # question
    if colmap["question"] is None:
        raise KeyError("Dataset must have a question/objection column (e.g., 'question' or 'objection').")
    out["question"] = df[colmap["question"]].astype(str).str.strip()
    # category
    if colmap["category"] is not None:
        out["category"] = df[colmap["category"]].astype(str).str.strip().replace({"": "objections/uncategorized"})
    else:
        out["category"] = "objections/uncategorized"
    # answer
    if colmap["answer"] is None:
        raise KeyError("Dataset must have a response/answer column (e.g., 'answer', 'response', or 'rebuttal').")
    out["answer"] = df[colmap["answer"]].astype(str).str.strip()

    # Drop any rows without minimal info
    out = out.dropna(subset=["question", "answer"])
    out = out[(out["question"] != "") & (out["answer"] != "")]

    # De-dup by question text
    out = out.drop_duplicates(subset=["question"]).reset_index(drop=True)

    return out, csv_path.name, original_cols


def pick_random_row(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        raise ValueError("No data loaded from the dataset after cleaning.")
    idx = random.randrange(len(df))
    return df.iloc[idx]


def main():
    st.set_page_config(page_title="Jay-Style Objection Rebuttal Practice")
    st.title("Jay-Style Objection Rebuttal Practice")
    st.write("Practice answering common objections in a voice consistent with Jay’s style and classic sales principles.")

    # Load data
    try:
        df, used_file, original_cols = load_dataset_auto()
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        st.info(f"Place one of these files next to this app: {', '.join(CANDIDATE_DATASETS)}")
        return

    # Sidebar info
    with st.sidebar:
        st.markdown("### Dataset")
        st.write(f"**Loaded file:** `{used_file}`")
        st.write(f"**Rows:** {len(df)}")
        st.write("**Detected columns:**")
        st.code(", ".join(original_cols), language="text")

        cats = sorted(df["category"].dropna().unique().tolist())
        selected = st.multiselect("Filter by category", cats, default=[])
        query = st.text_input("Search (question contains)", "")

    # Filtering
    filt = df.copy()
    if selected:
        filt = filt[filt["category"].isin(selected)]
    if query.strip():
        ql = query.strip().lower()
        filt = filt[filt["question"].str.lower().str.contains(ql)]

    st.write(f"Questions available after filters: **{len(filt)}**")
    if len(filt) == 0:
        st.warning("No rows match the current filters. Clear filters or adjust your search.")
        return

    # Interaction
    if "current_idx" not in st.session_state:
        st.session_state.current_idx = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎲 Random objection"):
            st.session_state.current_idx = random.randrange(len(filt))
    with col2:
        if st.button("⟲ Reset selection"):
            st.session_state.current_idx = None

    # Choose current row
    if st.session_state.current_idx is None:
        row = pick_random_row(filt)
    else:
        row = filt.iloc[st.session_state.current_idx]

    st.subheader("Objection")
    st.write(f"**Category:** {row['category']}")
    st.write(row["question"])

    st.subheader("Your response")
    user_resp = st.text_area("Type your rebuttal (or talk it out loud while you type notes):", height=140)

    with st.expander("Show suggested rebuttal (Jay-style + classic sales principles)"):
        st.markdown(row["answer"])

    st.caption("Tip: After you answer, reframe with an empathy opener, deliver a tight value frame, tie down with a short question, and ask for a next step.")

if __name__ == "__main__":
    main()
