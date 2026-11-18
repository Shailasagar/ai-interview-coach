import os
import tempfile
import streamlit as st
from resume_check import extract_resume_text, analyze_resume_vs_job

st.set_page_config(page_title="Resume Tools")
st.title("Resume Tools")
st.write("Compare your resume with a job description and find vague bullet points.")

resume = st.file_uploader("Resume (PDF)", type=["pdf"])
job = st.text_area("Paste the job description here", height=200)

if st.button("Analyze resume"):
    if resume is None or not job.strip():
        st.warning("Please upload a resume and paste a job description.")
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(resume.getvalue())
            path = tmp.name
        try:
            text = extract_resume_text(path)
        finally:
            os.remove(path)

        if len(text) < 50:
            st.error("Could not read text from this PDF. It may be a scanned image.")
        else:
            with st.spinner("Analyzing..."):
                result = analyze_resume_vs_job(text, job)

            if "error" in result:
                st.error(result["error"])
            else:
                st.metric("Match score (aid only, not a hiring verdict)", result["match_score"])
                st.write(result["summary"])

                c1, c2, c3 = st.columns(3)
                c1.subheader("Matched")
                c1.write(result["matched_skills"])
                c2.subheader("Missing")
                c2.write(result["missing_skills"])
                c3.subheader("Weak")
                c3.write(result["weak_skills"])

                st.subheader("Vague bullets to improve")
                for b in result["vague_bullets"]:
                    with st.expander(b["bullet"][:90]):
                        st.write("**Problem:**", b["problem"])
                        st.write("**Suggestion:**", b["suggestion"])
                st.caption(
                    "Only add numbers you can verify. Keyword matching is an aid, "
                    "not a guarantee of selection or rejection."
                )