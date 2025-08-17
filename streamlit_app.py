import streamlit as st
import pandas as pd
import pyttsx3
import tempfile
import os

# Load your objections + rebuttals dataset
# Make sure your CSV has columns: "Objection" and "Rebuttal"
df = pd.read_csv("objections.csv")

st.title("Agent Objection Handler 🎯")

# === Selector with radio buttons ===
objections = df["Objection"].tolist()
selected_objection = st.radio("Choose an Objection:", objections)

# Get rebuttal text
rebuttal_text = df.loc[df["Objection"] == selected_objection, "Rebuttal"].values[0]

st.subheader("Rebuttal")
st.write(rebuttal_text)

# === Tempo and Speed Controls ===
st.sidebar.header("Audio Settings")
rate = st.sidebar.slider("Speech Rate", min_value=100, max_value=300, value=180, step=10)
volume = st.sidebar.slider("Volume", min_value=0.0, max_value=1.0, value=1.0, step=0.1)

# === Text to Speech Function ===
def text_to_speech(text, rate=180, volume=1.0):
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)

    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    engine.save_to_file(text, tmpfile.name)
    engine.runAndWait()
    return tmpfile.name

# === Generate and Play Audio ===
if st.button("🔊 Play Rebuttal"):
    audio_file = text_to_speech(rebuttal_text, rate=rate, volume=volume)
    st.audio(audio_file, format="audio/mp3")
    os.remove(audio_file)
