import streamlit as st
import pandas as pd
from gtts import gTTS
import tempfile
import os

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("agent_rebuttals.csv")

df = load_data()

# App Title
st.title("Agent Objections & Rebuttals Library 🎯")

# Selector at top (radio buttons)
view_option = st.radio(
    "Choose what you want to browse:",
    ["Objections + Rebuttals", "SMS Snippets", "Email Subject Lines", "Email Bodies"]
)

# Display based on selection
if view_option == "Objections + Rebuttals":
    for idx, row in df.iterrows():
        st.markdown(f"### ❓ Objection: {row['Objection']}")
        st.markdown(f"**💡 Rebuttal:** {row['Rebuttal']}")

        col1, col2, col3 = st.columns([1,1,1])

        # Copy/download button
        with col1:
            st.code(row['Rebuttal'], language="text")

        with col2:
            st.download_button(
                "⬇️ Download Rebuttal",
                row['Rebuttal'],
                file_name=f"rebuttal_{idx}.txt"
            )

        # Audio playback using gTTS
        with col3:
            if st.button(f"🔊 Play Rebuttal #{idx}"):
                tts = gTTS(row['Rebuttal'])
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
                    tts.save(tmpfile.name)
                    audio_path = tmpfile.name
                st.audio(audio_path, format="audio/mp3")

elif view_option == "SMS Snippets" and "SMS" in df.columns:
    for idx, row in df.iterrows():
        if pd.notna(row["SMS"]):
            st.markdown(f"📱 **SMS #{idx}:** {row['SMS']}")
            st.code(row["SMS"], language="text")
            st.download_button(
                "⬇️ Download SMS",
                row["SMS"],
                file_name=f"sms_{idx}.txt"
            )

elif view_option == "Email Subject Lines" and "EmailSubject" in df.columns:
    for idx, row in df.iterrows():
        if pd.notna(row["EmailSubject"]):
            st.markdown(f"✉️ **Subject #{idx}:** {row['EmailSubject']}")
            st.code(row["EmailSubject"], language="text")

elif view_option == "Email Bodies" and "EmailBody" in df.columns:
    for idx, row in df.iterrows():
        if pd.notna(row["EmailBody"]):
            st.markdown(f"📧 **Email Body #{idx}:**")
            st.write(row["EmailBody"])
