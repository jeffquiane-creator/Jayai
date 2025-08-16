
import random
from pathlib import Path
import pandas as pd
import streamlit as st

# ---------------------- Config ----------------------
CANDIDATE_DATASETS = [
    # most specific first
    "Agent_Objection_Rebuttals_Dataset_Categorized - Agent_Objection_Rebuttals_Dataset_Categorized.csv.csv",
    "Agent_Objection_Rebuttals_Dataset_Categorized.csv",
    "training_dataset.csv",
]

# header aliases so we can normalize arbitrary CSVs
HEADER_ALIASES = {
    "filename": ["filename", "file", "source", "doc", "transcript"],
    "question": ["question", "objection", "prompt", "q", "objection_text", "question_text"],
    "category": ["category", "cat", "topic", "bucket", "group"],
    "answer":   ["answer", "response", "reply", "rebuttal", "a", "jay_style_answer", "talk_track"],
    # optional building blocks
    "technique_tags": ["technique_tags", "techniques", "tags"],
    "opener": ["opener", "empathy", "empathy_opener"],
    "frame": ["frame", "framing", "setup_line"],
    "value_points": ["value_points", "value", "bullets", "points"],
    "proof": ["proof", "credibility", "social_proof"],
    "tie_down": ["tie_down", "tie", "check_in"],
    "soft_close": ["soft_close", "softclose", "close"],
    "sms_snippet": ["sms_snippet", "sms", "text_snippet"],
    "email_subject": ["email_subject", "subject"],
    "email_body": ["email_body", "email", "body"],
}

# simple helpers
def _lowerstrip(s):
    return str(s).strip().lower()

def _find_col(cols_lower, aliases):
    for name in aliases:
        if name in cols_lower:
            return name
    return None

@st.cache_data(show_spinner=False)
def load_dataset(drop_dupes: bool = False):
    """Load first dataset found, normalize headers, and return cleaned DataFrame + metadata."""
    base = Path(__file__).parent
    csv_path = None
    for name in CANDIDATE_DATASETS:
        p = base / name
        if p.exists():
            csv_path = p
            break
    if csv_path is None:
        raise FileNotFoundError(f"Could not find a dataset. Expected one of: {', '.join(CANDIDATE_DATASETS)}")

    raw = pd.read_csv(csv_path)
    if raw.empty:
        raise ValueError(f"Dataset '{csv_path.name}' is empty.")

    # normalize headers
    raw_cols = list(raw.columns)
    norm = raw.copy()
    norm.columns = [_lowerstrip(c) for c in norm.columns]

    # build column map
    cmap = {}
    for key, aliases in HEADER_ALIASES.items():
        cmap[key] = _find_col(list(norm.columns), aliases)

    # minimally required
    if cmap["question"] is None or cmap["answer"] is None:
        raise KeyError("Dataset must include columns that map to 'question' and 'answer' (a.k.a. objection/rebuttal).")

    # construct output with safe defaults
    out = pd.DataFrame()
    out["filename"] = norm[cmap["filename"]].astype(str).str.strip() if cmap["filename"] else "jay_pocket_master"
    out.loc[out["filename"] == "", "filename"] = "jay_pocket_master"
    out["question"] = norm[cmap["question"]].astype(str).str.strip()
    out["category"] = norm[cmap["category"]].astype(str).str.strip() if cmap["category"] else "objections/uncategorized"
    out.loc[out["category"] == "", "category"] = "objections/uncategorized"
    out["answer"] = norm[cmap["answer"]].astype(str).str.strip()

    # optional building blocks (will be NaN if absent)
    opt_cols = ["technique_tags","opener","frame","value_points","proof","tie_down","soft_close","sms_snippet","email_subject","email_body"]
    for oc in opt_cols:
        col = cmap.get(oc)
        if col is not None and col in norm.columns:
            out[oc] = norm[col]
        else:
            out[oc] = ""

    # clean rows
    before = len(out)
    out = out.dropna(subset=["question","answer"])
    out = out[(out["question"] != "") & (out["answer"] != "")]
    after_clean = len(out)

    # optional dedupe
    if drop_dupes:
        q_norm = out["question"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
        out = out.loc[q_norm.drop_duplicates().index].reset_index(drop=True)

    return out.reset_index(drop=True), csv_path.name, raw_cols, before, after_clean

def parse_list_field(val, sep="|"):
    if pd.isna(val) or str(val).strip() == "":
        return []
    # allow | or ; as separators
    if ";" in str(val) and sep == "|":
        parts = str(val).split(";")
    else:
        parts = str(val).split(sep)
    return [p.strip() for p in parts if str(p).strip() != ""]

def compose_talk_track(opener, frame, value_points, proof, tie_down, soft_close):
    sections = []
    if opener: sections.append(opener.strip())
    body = ""
    if frame: body += frame.strip()
    if value_points:
        body += " " + " ".join(vp.strip() if vp.endswith(".") else vp.strip() + "." for vp in value_points)
    if proof: body += " " + (proof.strip() if proof.endswith(".") else proof.strip() + ".")
    if body: sections.append(body.strip())
    if tie_down: sections.append(tie_down.strip())
    if soft_close: sections.append(soft_close.strip())
    return " ".join([s for s in sections if s])

def random_pick(xlist, k=1):
    if not xlist:
        return []
    if k >= len(xlist):
        return xlist
    return random.sample(xlist, k=k)

def main():
    st.set_page_config(page_title="Jay-Style Pocket Objections (Practice + Compose)", layout="wide")
    st.title("Jay-Style Pocket Objections")
    st.caption("Search • Practice • Compose custom talk tracks with Jay-style delivery and top-tier sales frameworks.")

    # Sidebar controls
    with st.sidebar:
        st.markdown("### Dataset")
        drop_dupes = st.checkbox("Remove duplicate questions", value=False)
        try:
            df, used_file, raw_cols, before, after = load_dataset(drop_dupes=drop_dupes)
            st.success(f"Loaded: {used_file}")
            st.write(f"Rows (before clean): {before} • (after clean): {after}")
            st.write("Detected columns:")
            st.code(", ".join([str(c) for c in raw_cols]), language="text")
        except Exception as e:
            st.error(f"Failed to load dataset: {e}")
            st.info(f"Place one of these files next to this app: {', '.join(CANDIDATE_DATASETS)}")
            return

        # Filters
        cats = sorted(df["category"].dropna().unique().tolist())
        selected_cats = st.multiselect("Filter by category", cats, default=[])
        term = st.text_input("Search (question contains)", "")

    # Apply filters
    filt = df
    if selected_cats:
        filt = filt[filt["category"].isin(selected_cats)]
    if term.strip():
        tl = term.lower().strip()
        filt = filt[filt["question"].str.lower().str.contains(tl)]

    st.write(f"Questions available after filters: **{len(filt)}**")
    if len(filt) == 0:
        st.warning("No rows match the current filters. Clear filters or adjust your search.")
        return

    tab1, tab2 = st.tabs(["🛠 Practice", "🎙 Compose"])

    # ---------------------- Practice Tab ----------------------
    with tab1:
        colA, colB = st.columns([2, 3])
        with colA:
            if st.button("🎲 Random objection"):
                st.session_state.rand_idx = random.randrange(len(filt))
            if "rand_idx" not in st.session_state:
                st.session_state.rand_idx = 0
            row = filt.iloc[st.session_state.rand_idx]
            st.subheader("Objection")
            st.write(f"**Category:** {row['category']}")
            st.write(row["question"])

            st.subheader("Your response")
            st.text_area("Type your rebuttal (or talk it out):", key="practice_resp", height=140)

        with colB:
            with st.expander("Show suggested rebuttal (Jay-style + classic sales principles)", expanded=True):
                st.markdown(row["answer"])
            with st.expander("Building blocks (if present in dataset)"):
                st.write(f"**Opener:** {row.get('opener', '')}")
                st.write(f"**Frame:** {row.get('frame', '')}")
                st.write(f"**Value points:** {row.get('value_points', '')}")
                st.write(f"**Proof:** {row.get('proof', '')}")
                st.write(f"**Tie-down:** {row.get('tie_down', '')}")
                st.write(f"**Soft close:** {row.get('soft_close', '')}")
            with st.expander("Quick outreach snippets"):
                sms = row.get("sms_snippet", "")
                subj = row.get("email_subject", "")
                body = row.get("email_body", "")
                st.code(sms or "(no SMS snippet in dataset)", language="text")
                st.code(subj or "(no email subject in dataset)", language="text")
                st.code(body or "(no email body in dataset)", language="text")

    # ---------------------- Compose Tab ----------------------
    with tab2:
        left, right = st.columns([2, 3], gap="large")
        with left:
            # pick a specific objection
            idx = st.number_input("Row #", min_value=0, max_value=len(filt)-1, value=0, step=1)
            row = filt.iloc[idx]
            st.write(f"**Category:** {row['category']}")
            st.write(f"**Objection:** {row['question']}")
            st.write("---")

            # parse blocks
            vp_list = parse_list_field(row.get("value_points", ""), sep="|")
            # candidates for each block; if empty, offer fallback basic set
            opener_default = row.get("opener", "")
            frame_default = row.get("frame", "")
            proof_default = row.get("proof", "")
            tie_default = row.get("tie_down", "")
            close_default = row.get("soft_close", "")

            opener = st.text_input("Opener (empathy)", opener_default)
            frame = st.text_input("Frame (short setup)", frame_default)
            choose_n = st.slider("How many value points to include", 1, max(1, len(vp_list) if vp_list else 1), min(2, len(vp_list) if vp_list else 1))
            vps = st.multiselect("Select value points", vp_list if vp_list else [], default=vp_list[: min(2, len(vp_list))] if vp_list else [])
            if vp_list and len(vps) > choose_n:
                vps = vps[:choose_n]
            proof = st.text_input("Proof/credibility", proof_default)
            tie = st.text_input("Tie-down (short check-in)", tie_default)
            soft = st.text_input("Soft close (low-friction next step)", close_default)

            if st.button("Compose answer"):
                composed = compose_talk_track(opener, frame, vps, proof, tie, soft)
                st.session_state.composed = composed

            if st.button("Generate 3 variations"):
                variations = []
                for _ in range(3):
                    pick_vps = random_pick(vp_list, k=min(2, len(vp_list))) if vp_list else vps
                    variations.append(compose_talk_track(
                        opener or row.get("opener", ""),
                        frame or row.get("frame",""),
                        pick_vps,
                        proof or row.get("proof",""),
                        tie or row.get("tie_down",""),
                        soft or row.get("soft_close",""),
                    ))
                st.session_state.variations = variations

        with right:
            st.subheader("Composed talk track")
            st.text_area("Your composed answer", value=st.session_state.get("composed", ""), height=220, key="composed_area")
            st.caption("Tip: Keep sentences tight. Empathy → concise value → proof → tiny tie-down → soft next step.")

            if "variations" in st.session_state:
                st.subheader("Alternates")
                for i, v in enumerate(st.session_state["variations"], start=1):
                    st.code(v, language="text")

    st.caption("© Pocket Objections — Jay-style practice + composition")

if __name__ == "__main__":
    main()
