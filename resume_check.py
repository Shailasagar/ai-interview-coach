import json, time, random
import pdfplumber
from feedback import client, MODELS


def extract_resume_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text.strip()


def check_resume_match(transcript, resume_text):
    prompt = f"""You are checking an interview answer against the candidate's resume.

Resume:
{resume_text}

Spoken answer:
{transcript}

Find which claims in the spoken answer are supported by the resume, which are not found in the resume, and which important resume items were not mentioned. The spoken answer comes from speech-to-text, so ignore small spelling mistakes in names.
Reply ONLY with JSON in this format, no other text:
{{"supported": [], "not_found_in_resume": [], "missed_highlights": [], "summary": ""}}"""

    for model in MODELS:
        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                reply = response.choices[0].message.content
                reply = reply.replace("```json", "").replace("```", "").strip()
                return json.loads(reply)
            except Exception as e:
                print(f"{model} attempt {attempt + 1} failed: {str(e)[:60]}")
                if "429" in str(e) or "Connection" in str(e):
                    break
                time.sleep(5)

    return {"error": "All models are busy. Try again later."}


def generate_questions(resume_text, count=5):
    angles = [
        "a specific project and the candidate's personal contribution",
        "an internship or work experience and what they achieved",
        "a technical skill or tool listed and how they used it",
        "a challenge, trade-off or mistake in a project",
        "teamwork, leadership or initiative",
        "an achievement, certification or result that can be explained in detail",
        "career goals and why this field",
    ]
    chosen = ", ".join(random.sample(angles, 4))

    prompt = f"""You are an interviewer preparing a mock interview.

Resume:
{resume_text}

Write {count} interview questions for this candidate. Rules:
- Question 1 is a friendly opener, such as an introduction or motivation question, worded differently every time.
- The other questions must refer to specific items from the resume (named projects, internships, skills).
- Focus this time on: {chosen}.
- Each question must be one or two sentences and answerable in about 1-2 minutes.
- Variation seed: {random.randint(1000, 9999)}. Do not use the most obvious questions.
Reply ONLY with a JSON list of {count} strings, no other text."""

    for model in MODELS:
        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                )
                reply = response.choices[0].message.content
                reply = reply.replace("```json", "").replace("```", "").strip()
                questions = json.loads(reply)
                if isinstance(questions, list) and len(questions) >= count:
                    return [str(q) for q in questions[:count]]
            except Exception as e:
                print(f"{model} question attempt {attempt + 1} failed: {str(e)[:60]}")
                if "429" in str(e) or "Connection" in str(e):
                    break
                time.sleep(5)
    return None
def analyze_resume_vs_job(resume_text, job_description):
    prompt = f"""You are a resume reviewer.

Resume:
{resume_text}

Job description:
{job_description}

Tasks:
1. List the skills/keywords from the job description that the resume clearly shows (matched_skills).
2. List relevant skills/keywords from the job description that are missing from the resume (missing_skills).
3. List skills that appear in the resume but only weakly, with no project or result behind them (weak_skills).
4. Find up to 5 resume bullets with vague impact and no measurable evidence. For each, give the bullet, what is vague about it, and a suggestion. Suggest adding numbers ONLY if the candidate can verify them, and never invent a number.
5. Give a one-paragraph summary and an overall match score from 0 to 100.

This is a coaching aid, not a hiring decision.
Reply ONLY with JSON in this format, no other text:
{{"match_score": 0, "matched_skills": [], "missing_skills": [], "weak_skills": [], "vague_bullets": [{{"bullet": "", "problem": "", "suggestion": ""}}], "summary": ""}}"""

    for model in MODELS:
        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                reply = response.choices[0].message.content
                reply = reply.replace("```json", "").replace("```", "").strip()
                return json.loads(reply)
            except Exception as e:
                print(f"{model} resume-job attempt {attempt + 1} failed: {str(e)[:60]}")
                if "429" in str(e) or "Connection" in str(e):
                    break
                time.sleep(5)
    return {"error": "All models are busy. Try again later."}