import os
import tempfile
import streamlit as st
from pipeline import run_pipeline

st.set_page_config(page_title="Mini-Mock Interview")
st.title("Mini-Mock Interview")

QUESTIONS = [
    "Tell me about yourself.",
    "Why did you choose Computer Science and Engineering?",
    "Describe a project you are proud of and your role in it.",
    "Explain a technical concept from your project in simple words.",
    "Where do you see yourself in five years, and why should we hire you?",
]

if "index" not in st.session_state:
    st.session_state.index = 0
    st.session_state.reports = []
    st.session_state.resume_bytes = None


def save_temp(data, suffix):
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        return tmp.name


total = len(QUESTIONS)
i = st.session_state.index

if i == 0 and not st.session_state.reports:
    resume = st.file_uploader("Resume (PDF, optional)", type=["pdf"])
    st.session_state.resume_bytes = resume.getvalue() if resume else None

if i < total:
    st.progress(i / total)
    st.subheader(f"Question {i + 1} of {total}")
    st.write(QUESTIONS[i])

    audio = st.audio_input("Record your answer", key=f"audio_{i}")

    if st.button("Submit answer"):
        if audio is None:
            st.warning("Please record your answer first.")
        else:
            audio_path = save_temp(audio.getvalue(), ".wav")
            resume_bytes = st.session_state.resume_bytes
            resume_path = save_temp(resume_bytes, ".pdf") if resume_bytes else None
            try:
                with st.spinner("Analyzing your answer... about a minute."):
                    report = run_pipeline(audio_path, QUESTIONS[i], resume_path)
            finally:
                os.remove(audio_path)
                if resume_path:
                    os.remove(resume_path)
            st.session_state.reports.append(report)
            st.session_state.index += 1
            st.rerun()
else:
    reports = st.session_state.reports
    st.success("Mock interview complete! Here is your report.")

    scored = [r["feedback"] for r in reports if "error" not in r["feedback"]]

    def avg(key):
        if not scored:
            return "n/a"
        return round(sum(f[key] for f in scored) / len(scored), 1)

    c1, c2, c3 = st.columns(3)
    c1.metric("Avg relevance", avg("relevance"))
    c2.metric("Avg structure", avg("structure"))
    c3.metric("Avg depth", avg("depth"))

    avg_wpm = round(sum(r["voice"]["wpm"] for r in reports) / len(reports))
    total_pauses = sum(len(r["voice"]["pauses"]) for r in reports)
    total_fillers = sum(sum(r["voice"]["fillers"].values()) for r in reports)

    d1, d2, d3 = st.columns(3)
    d1.metric("Avg WPM", avg_wpm)
    d2.metric("Long pauses", total_pauses)
    d3.metric("Filler words", total_fillers)

    st.subheader("Question by question")
    for n, r in enumerate(reports, 1):
        with st.expander(f"Q{n}: {r['question']}"):
            st.write("**Transcript:**", r["voice"]["transcript"])
            st.write(f"**WPM:** {r['voice']['wpm']}")
            for p in r["voice"]["pauses"]:
                st.write(f"Pause at {p['at_seconds']}s ({p['length_seconds']}s)")
            fb = r["feedback"]
            if "error" in fb:
                st.error(fb["error"])
            else:
                st.write(
                    f"**Scores:** relevance {fb['relevance']}, "
                    f"structure {fb['structure']}, depth {fb['depth']}"
                )
                st.write("**Strengths:**", fb["strengths"])
                st.write("**Improvements:**", fb["improvements"])
            rc = r.get("resume_check")
            if rc and "error" not in rc:
                st.write("**Resume check:**", rc["summary"])

    if st.button("Start a new mock interview"):
        for key in ["index", "reports", "resume_bytes"]:
            st.session_state.pop(key, None)
        st.rerun()