import os
import tempfile
import streamlit as st
from pipeline import run_pipeline

st.set_page_config(page_title="AI Interview Coach")
st.title("AI Interview Coach")

QUESTIONS = [
    "Tell me about yourself.",
    "What are your strengths and weaknesses?",
    "Describe a challenging project you worked on.",
    "Why should we hire you?",
]
question = st.selectbox("Choose a question", QUESTIONS)

recorded = st.audio_input("Record your answer")
uploaded = st.file_uploader("...or upload an audio file", type=["mp3", "wav", "m4a"])
resume = st.file_uploader("Resume (PDF, optional)", type=["pdf"])

audio_file = recorded or uploaded


def save_temp(file, suffix):
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.getvalue())
        return tmp.name


if st.button("Analyze my answer"):
    if audio_file is None:
        st.warning("Please record or upload an answer first.")
    else:
        name = getattr(audio_file, "name", "answer.wav")
        audio_path = save_temp(audio_file, os.path.splitext(name)[1] or ".wav")
        resume_path = save_temp(resume, ".pdf") if resume else None

        try:
            with st.spinner("Analyzing... this can take a minute."):
                report = run_pipeline(audio_path, question, resume_path)
        finally:
            os.remove(audio_path)
            if resume_path:
                os.remove(resume_path)

        voice = report["voice"]
        feedback = report["feedback"]

        st.subheader("Transcript")
        st.write(voice["transcript"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Words per minute", voice["wpm"])
        c2.metric("Words", voice["word_count"])
        c3.metric("Long pauses", len(voice["pauses"]))

        st.subheader("Filler words")
        st.write(voice["fillers"])

        if voice["pauses"]:
            st.subheader("Pauses")
            for p in voice["pauses"]:
                st.write(f"At {p['at_seconds']}s: {p['length_seconds']}s pause")

        st.subheader("AI feedback")
        if "error" in feedback:
            st.error(feedback["error"])
        else:
            s1, s2, s3 = st.columns(3)
            s1.metric("Relevance", feedback["relevance"])
            s2.metric("Structure", feedback["structure"])
            s3.metric("Depth", feedback["depth"])
            st.write("**Strengths:**", feedback["strengths"])
            st.write("**Improvements:**", feedback["improvements"])

        if "resume_check" in report:
            st.subheader("Resume check")
            rc = report["resume_check"]
            if "error" in rc:
                st.error(rc["error"])
            else:
                st.write("**Supported by resume:**", rc["supported"])
                st.write("**Not found in resume:**", rc["not_found_in_resume"])
                st.write("**Highlights you missed:**", rc["missed_highlights"])
                st.write(rc["summary"])