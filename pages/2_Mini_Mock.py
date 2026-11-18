import os
import random
import tempfile
import streamlit as st
from pipeline import run_pipeline
from resume_check import extract_resume_text, generate_questions
from datetime import datetime
st.set_page_config(page_title="Mini-Mock Interview")
st.title("Mini-Mock Interview")

NUM_QUESTIONS = 5

DEFAULT_POOL = [
    "Tell me about yourself.",
    "Why did you choose Computer Science and Engineering?",
    "Describe a project you are proud of and your role in it.",
    "Explain a technical concept from your studies in simple words.",
    "Tell me about a time you faced a difficult problem and how you solved it.",
    "What are your strengths and weaknesses?",
    "Describe a time you worked in a team. What was your contribution?",
    "What did you learn from your internship or a recent project?",
    "Where do you see yourself in five years?",
    "Why should we hire you?",
]


def save_temp(data, suffix):
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        return tmp.name


# ---------- Setup screen ----------
if "questions" not in st.session_state:
    st.write(
        "Upload your resume to get questions based on it, "
        "or skip it for a random set of general questions."
    )
    resume = st.file_uploader("Resume (PDF, optional)", type=["pdf"])

    if st.button("Start mock interview"):
        resume_bytes = resume.getvalue() if resume else None
        questions = None
        notice = ""

        if resume_bytes:
            path = save_temp(resume_bytes, ".pdf")
            try:
                with st.spinner("Reading your resume and preparing questions..."):
                    text = extract_resume_text(path)
                    questions = generate_questions(text, NUM_QUESTIONS)
            finally:
                os.remove(path)
            if not questions:
                notice = "Resume-based questions are unavailable right now, so general questions are used."

        if not questions:
            questions = random.sample(DEFAULT_POOL, NUM_QUESTIONS)

        st.session_state.questions = questions
        st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        st.session_state.resume_bytes = resume_bytes
        st.session_state.index = 0
        st.session_state.reports = []
        st.session_state.notice = notice
        st.rerun()

    st.stop()

# ---------- Interview ----------
QUESTIONS = st.session_state.questions
total = len(QUESTIONS)
i = st.session_state.index

if st.session_state.get("notice"):
    st.info(st.session_state.notice)

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
                    report = run_pipeline(
                        audio_path, QUESTIONS[i], resume_path,
                        session_id=st.session_state.session_id, mode="mock",
                    )
            finally:
                os.remove(audio_path)
                if resume_path:
                    os.remove(resume_path)
            st.session_state.reports.append(report)
            st.session_state.index += 1
            st.rerun()

# ---------- Final report ----------
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
            ac = r["voice"].get("acoustics")
            if ac and "error" not in ac:
                st.write(f"**Pitch:** {ac['pitch_note']}")
                st.write(f"**Volume:** {ac['volume_note']}")
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
        for key in ["questions", "index", "reports", "resume_bytes", "notice", "session_id"]:
            st.session_state.pop(key, None)
        st.rerun()