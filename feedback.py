import os, json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

question = "Tell me about yourself."
transcript = open("transcript.txt", encoding="utf-8").read()

prompt = f"""You are an interview coach.
Question: {question}
Candidate's answer: {transcript}

Score the answer from 1-10 for relevance, structure and depth.
Reply ONLY with JSON in this format, no other text:
{{"relevance": 0, "structure": 0, "depth": 0, "strengths": "", "improvements": ""}}"""

response = client.chat.completions.create(
    model=os.getenv("GEMINI_MODEL"),
    messages=[{"role": "user", "content": prompt}],
)

reply = response.choices[0].message.content
reply = reply.replace("```json", "").replace("```", "").strip()
data = json.loads(reply)

print("Relevance:", data["relevance"])
print("Structure:", data["structure"])
print("Depth:", data["depth"])
print("Strengths:", data["strengths"])
print("Improvements:", data["improvements"])