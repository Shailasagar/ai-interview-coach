import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

for model in ["gemini-4-hydrogen", "gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]:
    try:
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say OK"}],
        )
        print(model, "-> WORKS")
    except Exception as e:
        print(model, "-> failed:", str(e)[:60])