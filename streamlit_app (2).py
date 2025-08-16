"""
Streamlit App for Jay 3‑Way Call Practice
-----------------------------------------

This Streamlit application provides a web interface for practising
conversation handling using the labelled dataset of questions and answers
extracted from Jay Kinder’s three‑way call transcripts.  It randomly
selects a question, displays it to the user, allows the user to type a
response, and then reveals Jay’s suggested answer.  The app can be
deployed to Streamlit Community Cloud (https://streamlit.io/cloud/) to
generate a shareable link that anyone can access via a web browser.

To use this app:

1. Make sure you have the ``training_dataset.csv`` file in the same
   directory as this script or supply a custom path using the
   ``--dataset`` query parameter.

2. Install Streamlit if you haven’t already:

   ::

       pip install streamlit pandas

3. Run the app locally with:

   ::

       streamlit run streamlit_app.py

4. To deploy the app for others to use, commit this script and the
   dataset to a GitHub repository, then use Streamlit’s Community Cloud
   to create a new app pointing to ``streamlit_app.py``.  Streamlit
   Cloud will generate a URL you can share.
"""

import csv
import os
import random
from dataclasses import dataclass
from typing import List

import streamlit as st


@dataclass
class QAItem:
    filename: str
    question: str
    category: str
    answer: str


def load_dataset(path: str) -> List[QAItem]:
    """
    Load the labelled questions from the CSV dataset.

    This helper attempts to be resilient to minor formatting issues in the
    CSV such as extra whitespace around header names.  It reads each
    row into a dictionary, strips whitespace from the keys and then
    extracts the expected fields.  Rows missing the required fields
    will be skipped with a warning.

    Parameters
    ----------
    path : str
        The filesystem path to the CSV file.

    Returns
    -------
    List[QAItem]
        A list of parsed question/answer entries.
    """
    qa_list: List[QAItem] = []
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Build a cleaned version of the row.  Some CSV rows may have
            # more fields than there are header columns, in which case
            # csv.DictReader inserts the extra data under the key None.  We
            # filter those out and also strip whitespace from string keys.
            clean_row = {}
            for key, value in row.items():
                # Skip entries where key is None (extra columns) or not a string.
                if key is None:
                    continue
                # Strip whitespace from keys to handle accidental spaces.
                if isinstance(key, str):
                    clean_key = key.strip()
                else:
                    clean_key = key
                clean_row[clean_key] = value
            # Pull fields using get() to avoid KeyError.  Only filename and question
            # are strictly required; category and answer may be empty strings in the
            # dataset.  If a required field is missing (None), skip the row.
            filename = clean_row.get('filename')
            question = clean_row.get('question')
            category = clean_row.get('category', '')
            answer = clean_row.get('answer', '')
            if filename is None or question is None:
                continue
            qa_list.append(
                QAItem(
                    filename=filename,
                    question=question,
                    category=category,
                    answer=answer,
                )
            )
    return qa_list


def main() -> None:
    """Entry point for the Streamlit app."""
    st.set_page_config(page_title="Jay Call Practice Simulator")
    st.title("Jay Call Practice Simulator")
    st.write("Practice answering common questions like Jay Kinder.")

    # Hard‑code the dataset path relative to this file.  When deploying to
    # Streamlit Community Cloud or running locally, place 'training_dataset.csv'
    # in the same directory as this script.  If you wish to use a different
    # dataset file, modify the filename here.
    default_dataset = os.path.join(os.path.dirname(__file__), 'training_dataset.csv')

    # Load dataset once and cache it
    @st.cache_data
    def get_qa_list(path: str) -> List[QAItem]:
        return load_dataset(path)

    try:
        qa_list = get_qa_list(default_dataset)
    except FileNotFoundError:
        st.error(
            "Dataset not found. Ensure 'training_dataset.csv' is in the same directory as the app "
            "or update the dataset path in the code."
        )
        return
    except Exception as exc:
        st.error(f"Failed to load dataset: {exc}")
        return
    # If no entries were loaded, show a helpful error message.
    if not qa_list:
        st.error(
            "No data loaded from the dataset. Please verify that 'training_dataset.csv' contains at least one "
            "question and that the CSV headers are correct (filename, question, category, answer)."
        )
        return

    # Initialize session state for the current question and the user's response
    if 'current_qa' not in st.session_state:
        st.session_state['current_qa'] = None
        st.session_state['user_response'] = ''

    # Button to get a new question
    if st.button("Get a new question") or st.session_state['current_qa'] is None:
        st.session_state['current_qa'] = random.choice(qa_list)
        st.session_state['user_response'] = ''

    current_qa: QAItem = st.session_state['current_qa']
    if current_qa:
        st.subheader(f"Category: {current_qa.category}")
        st.write(f"**Question:** {current_qa.question}")
        # Text area for user response
        st.session_state['user_response'] = st.text_area(
            "Your Answer",
            value=st.session_state.get('user_response', ''),
            height=100,
        )
        # Button to reveal Jay's answer
        if st.button("Show Jay's Answer"):
            st.write("**Jay's Suggested Answer:**")
            st.write(current_qa.answer if current_qa.answer else "(No answer recorded)")


if __name__ == '__main__':
    main()