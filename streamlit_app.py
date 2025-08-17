import streamlit as st
import pandas as pd

# Load dataset
@st.cache_data
def load_data(file):
    return pd.read_excel(file)

st.title("🚀 Funnel Pilot Rebuttal & Brokerage Hub")

# Upload
uploaded_file = st.file_uploader("Upload your dataset", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Dataset selector
    option = st.radio("Choose dataset view:", ["All", "Favorites"])

    # Search
    search = st.text_input("Search for an objection/question")
    if search:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

    # Initialize favorites in session state
    if "favorites" not in st.session_state:
        st.session_state["favorites"] = set()

    if option == "Favorites":
        df = df[df.index.isin(st.session_state["favorites"])]

    # Display
    for idx, row in df.iterrows():
        st.markdown(f"**❌ {row.get('Objection', row.get('Question',''))}**")
        st.write(row.get("Rebuttal", ""))

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📋 Copy", key=f"copy{idx}"):
                st.write("✅ Copied (simulate clipboard here)")  # Streamlit can't directly copy to clipboard
        with col2:
            text = row.get("Rebuttal", "")
            st.download_button("💾 Download", text, file_name=f"rebuttal_{idx}.txt")
        with col3:
            fav_label = "★ Unfavorite" if idx in st.session_state["favorites"] else "☆ Favorite"
            if st.button(fav_label, key=f"fav{idx}"):
                if idx in st.session_state["favorites"]:
                    st.session_state["favorites"].remove(idx)
                else:
                    st.session_state["favorites"].add(idx)

else:
    st.warning("Please upload Agent_Objections_Rebuttals.xlsx or a CSV file.")
