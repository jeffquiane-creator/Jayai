
import streamlit as st
import pandas as pd
import pyttsx3
import io

# Initialize TTS engine
engine = pyttsx3.init()

# App title
st.set_page_config(page_title="Agent Objections Hub", layout="wide")
st.title("🎯 Agent Objection Handler with Audio + Favorites")

# File uploader
uploaded_file = st.file_uploader("Upload your objections CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Remove 's.MS' column if it exists
    if "s.MS" in df.columns:
        df = df.drop(columns=["s.MS"])

    if "SMS" not in df.columns:
        df["SMS"] = ""

    if "Rebuttal" not in df.columns:
        st.error("CSV must contain a 'Rebuttal' column.")
    else:
        st.success("Data loaded successfully!")

        # Session state for favorites
        if "favorites" not in st.session_state:
            st.session_state.favorites = []

        # Search bar
        query = st.text_input("Search objections or rebuttals")
        if query:
            results = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)]
        else:
            results = df

        # Display results
        for i, row in results.iterrows():
            st.markdown(f"### ❓ Objection: {row['Objection'] if 'Objection' in row else 'N/A'}")
            st.write(f"**Rebuttal:** {row['Rebuttal']}")

            # Buttons
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button(f"📋 Copy Rebuttal {i}"):
                    st.write("✅ Rebuttal copied! (Use Ctrl+C manually here)")  

            with col2:
                if st.button(f"🔊 Play Rebuttal {i}"):
                    engine.say(row['Rebuttal'])
                    engine.runAndWait()

            with col3:
                if st.button(f"⭐ Favorite {i}"):
                    st.session_state.favorites.append(row.to_dict())
                    st.success("Added to favorites!")

            with col4:
                if st.download_button("⬇️ Download Rebuttal", data=row['Rebuttal'], file_name="rebuttal.txt"):
                    st.write("Downloaded.")

        # Favorites section
        st.subheader("⭐ Favorites")
        if st.session_state.favorites:
            fav_df = pd.DataFrame(st.session_state.favorites)
            st.dataframe(fav_df)
            buffer = io.BytesIO()
            fav_df.to_csv(buffer, index=False)
            st.download_button("⬇️ Download Favorites CSV", data=buffer, file_name="favorites.csv", mime="text/csv")
        else:
            st.info("No favorites yet.")
