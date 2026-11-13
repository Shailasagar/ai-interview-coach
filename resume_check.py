import json, time
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
        if not model:
            continue
        for attempt in range(3):
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
                if "429" in str(e):
                    break  # rate limited: go to the next model
                time.sleep(10 * (attempt + 1))

    return {"error": "All models are busy. Try again later."}