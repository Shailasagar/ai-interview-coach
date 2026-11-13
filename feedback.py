import os, json, time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

MODELS = [
    os.getenv("GEMINI_MODEL"),
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
]

def get_feedback(question, transcript):
    prompt = f"""You are an interview coach.
Question: {question}
Candidate's answer: {transcript}

Score the answer from 1-10 for relevance, structure and depth.
Reply ONLY with JSON in this format, no other text:
{{"relevance": 0, "structure": 0, "depth": 0, "strengths": "", "improvements": ""}}"""

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
                print(f"{model} attempt {attempt + 1} failed: {str(e)[:100]}")
                time.sleep(3)

    return {"error": "All models are busy. Try again later."}