
import random
from pathlib import Path
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------- Config ----------------
CANDIDATE_DATASETS = [
    # Your primary file
    "Objection_Rebuttal_Master_500 (1).csv",
    # Other common alternates / earlier files
    "Objection_Rebuttal_Master_500.csv",
    "100_Unique_Objections___Rebuttals - 100_Unique_Objections___Rebuttals.csv (3).csv",
    "100_Unique_Objections___Rebuttals.csv",
    "Agent_Objection_Rebuttals_Dataset_Categorized.csv",
    "training_dataset.csv",
]

HEADER_ALIASES = {
    # Support slash headers and common variants
    "question": ["objection/question", "objection", "question", "prompt", "q"],
    "answer":   ["rebuttal/answer", "rebuttal", "answer", "response", "reply"],
    "category": ["category", "topic", "bucket"],
    "tags":     ["tags", "keywords", "labels"],
    # Optional snippet columns
    "sms": ["sms", "sms_snippet", "text_snippet"],
    "email_subject": ["emailsubject", "email_subject", "subject"],
    "email_body": ["emailbody", "email_body", "email", "body"],
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
    for v in series.fillna('').astype(str):
        if not v.strip():
            continue
        # normalize separators
        tmp = v.replace('|', ',').replace(';', ',')
        for t in tmp.split(','):
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
    raw = raw.dropna(axis=1, how='all')  # drop fully empty columns
    if raw.empty:
        raise ValueError(f"Dataset '{csv_path.name}' is empty.")

    # map columns
    q_col = _find_col(list(raw.columns), HEADER_ALIASES['question'])
    a_col = _find_col(list(raw.columns), HEADER_ALIASES['answer'])
    c_col = _find_col(list(raw.columns), HEADER_ALIASES['category'])
    t_col = _find_col(list(raw.columns), HEADER_ALIASES['tags'])
    sms_col = _find_col(list(raw.columns), HEADER_ALIASES['sms'])
    subj_col = _find_col(list(raw.columns), HEADER_ALIASES['email_subject'])
    body_col = _find_col(list(raw.columns), HEADER_ALIASES['email_body'])

    if q_col is None or a_col is None:
        raise KeyError('Dataset needs columns for objection/question and rebuttal/answer.')

    df = pd.DataFrame({
        'question': raw[q_col].astype(str).str.strip(),
        'answer':   raw[a_col].astype(str).str.strip(),
    })
    df['category'] = raw[c_col].fillna('').astype(str).str.strip() if c_col else ''
    df['tags'] = raw[t_col].fillna('').astype(str).str.strip() if t_col else ''

    # Optional snippets
    df['SMS'] = raw[sms_col].fillna('').astype(str).str.strip() if sms_col else ''
    df['EmailSubject'] = raw[subj_col].fillna('').astype(str).str.strip() if subj_col else ''
    df['EmailBody'] = raw[body_col].fillna('').astype(str).str.strip() if body_col else ''

    # Clean minimal
    df = df[(df['question'] != '') & (df['answer'] != '')].reset_index(drop=True)
    return df, csv_path.name

def copy_button(label: str, text: str, key: str):
    'Small JS copy-to-clipboard button without external packages.'
    safe = json.dumps(text)  # escape quotes/newlines safely
    html = f'''
    <button id="{key}" style="padding:6px 10px; font-size:12px; margin-right:6px; cursor:pointer;">
      {label}
    </button>
    <script>
    const btn_{key.replace('-', '_')} = document.getElementById("{key}");
    btn_{key.replace('-', '_')}.onclick = async () => {{
        try {{
            await navigator.clipboard.writeText({safe});
        }} catch (e) {{
            console.log(e);
        }}
    }};
    </script>
    '''
    components.html(html, height=40)

def main():
    st.set_page_config(page_title='Pocket Objections (Simple)', layout='centered')
    st.title('Pocket Objections — Simple')
    st.caption('Search • Filter • Read the rebuttal. No clutter.')

    # Load
    try:
        df, used_file = load_data()
    except Exception as e:
        st.error(f'Failed to load dataset: {e}')
        return

    # --- Sidebar: simple filters ---
    with st.sidebar:
        st.markdown('### Filters')
        st.write(f'Using: `{used_file}`')
        term = st.text_input('Search in objection', '')

        # Category filter (only if present)
        cats = sorted([c for c in df['category'].unique().tolist() if c])
        category = None
        if len(cats) > 0:
            category = st.selectbox('Category', ['All'] + cats, index=0)

        # Tag filter (only if present)
        tag_tokens = _parse_tags(df['tags']) if 'tags' in df.columns else []
        tag = None
        if len(tag_tokens) > 0:
            tag = st.selectbox('Tag', ['All'] + tag_tokens, index=0)

    # --- Apply filters ---
    filt = df
    if term.strip():
        tl = term.strip().lower()
        filt = filt[filt['question'].str.lower().str.contains(tl)]
    if category and category != 'All':
        filt = filt[filt['category'] == category]
    if tag and tag != 'All':
        # normalize and token-match each row's tags
        def has_tag(cell: str) -> bool:
            cell = (cell or '').lower().replace('|', ',').replace(';', ',')
            toks = [t.strip() for t in cell.split(',') if t.strip()]
            return tag.lower() in toks
        filt = filt[filt['tags'].apply(has_tag)]

    count = len(filt)
    st.write(f'Matches: **{count}**')
    if count == 0:
        st.warning('No results. Try clearing filters or a different search.')
        return

    # --- Selection ---
    options = [f"{i}. {q[:120]}" for i, q in enumerate(filt['question'].tolist())]
    selected = st.selectbox('Pick an objection', options, index=0, label_visibility='collapsed')
    sel_idx = int(selected.split('. ', 1)[0])
    row = filt.iloc[sel_idx]

    # --- Display ---
    st.subheader('Objection')
    if row['category']:
        st.write(f"**Category:** {row['category']}")
    st.write(row['question'])

    st.subheader('Rebuttal')
    st.markdown(row['answer'])

    # --- One‑click snippets (if present) ---
    has_sms = isinstance(row.get('SMS',''), str) and row.get('SMS','').strip() != ''
    has_email = (isinstance(row.get('EmailSubject',''), str) and row.get('EmailSubject','').strip() != '') or                 (isinstance(row.get('EmailBody',''), str) and row.get('EmailBody','').strip() != '')

    if has_sms or has_email:
        st.markdown('---')
        st.subheader('Snippets')

        if has_sms:
            st.markdown('**SMS**')
            st.code(row['SMS'], language='text')
            copy_button('Copy SMS', row['SMS'], key='copy-sms')
            st.download_button('Download SMS.txt', data=row['SMS'].encode('utf-8'),
                               file_name='sms_snippet.txt', mime='text/plain')

        if has_email:
            st.markdown('**Email**')
            subj = row.get('EmailSubject','').strip()
            body = row.get('EmailBody','').strip()
            preview = (subj + '\n\n' + body).strip()
            st.code(preview or '(no content)', language='text')
            if subj:
                copy_button('Copy Subject', subj, key='copy-subj')
            if body:
                copy_button('Copy Body', body, key='copy-body')
            st.download_button('Download Email.txt', data=preview.encode('utf-8'),
                               file_name='email_snippet.txt', mime='text/plain')

    st.caption('Empathy → short frame → value → tie‑down → next step.')

if __name__ == '__main__':
    main()
