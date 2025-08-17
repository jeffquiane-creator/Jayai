import streamlit as st
import pandas as pd
import pyttsx3
import tempfile
import base64
import os

# Load objections/rebuttals from CSV
@st.cache_data
def load_data():
    df = pd.read_csv("Objection_Rebuttal_Master_500 (1).csv")
    # Ensure column names match
    df = df.rename(columns=lambda x: x.strip())
    return df

data = load_data()

# Initialize session state for favorites
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []

st.title("🎯 Agent Objection Handler")

# Objection selector
selected_objection = st.radio(
    "Choose an objection:",
    data["Objection"].dropna().unique()
)

# Lookup rebuttal
rebuttal = ""
if selected_objection:
    rebuttal = data.loc[data["Objection"] == selected_objection, "Rebuttal"].values[0]
    st.subheader("💡 Rebuttal")
    st.write(rebuttal)

    # Copy to clipboard (browser safe via text area)
    st.text_area("Copy Rebuttal:", rebuttal, height=100)

    # Download as text
    b64 = base64.b64encode(rebuttal.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="rebuttal.txt">⬇️ Download Rebuttal</a>'
    st.markdown(href, unsafe_allow_html=True)

    # Add to favorites
    if st.button("⭐ Add to Favorites"):
        if selected_objection not in [f[0] for f in st.session_state["favorites"]]:
            st.session_state["favorites"].append((selected_objection, rebuttal))
            st.success("Added to favorites!")

# Show favorites
if st.session_state["favorites"]:
    st.subheader("⭐ Favorites")
    for obj, reb in st.session_state["favorites"]:
        with st.expander(obj):
            st.write(reb)

# Audio playback with tempo/speed adjustment
st.subheader("🔊 Text-to-Speech Rebuttal")

speech_rate = st.slider("Adjust Speed (words per minute):", 100, 250, 150, 10)

if st.button("▶️ Play Rebuttal Audio") and rebuttal:
    engine = pyttsx3.init()
    engine.setProperty("rate", speech_rate)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_file = fp.name
    engine.save_to_file(rebuttal, temp_file)
    engine.runAndWait()

    audio_file = open(temp_file, "rb")
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format="audio/mp3")
    audio_file.close()
    os.remove(temp_file)
