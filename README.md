# AI Interview Coach

Practice interviews with voice analysis, AI feedback and resume checks.

## Setup (Windows)
1. Install Python (same version as the project author), Git and VS Code.
2. Install ffmpeg: open Command Prompt and run `winget install ffmpeg`, then reopen the terminal.
3. Download the project:
   git clone https://github.com/Shailasagar/ai-interview-coach.git
   cd ai-interview-coach
4. Create and activate a virtual environment:
   python -m venv venv
   venv\Scripts\activate
5. Install libraries (takes several minutes):
   pip install -r requirements.txt
6. Get a free Gemini API key at aistudio.google.com ("Get API key").
7. Create a file named `.env` in the project folder:
   GEMINI_API_KEY=your-own-key
   GEMINI_MODEL=gemini-3.5-flash-lite
8. Run:
   streamlit run app.py
   Open http://localhost:8501 and allow microphone access.

## Notes
- The first answer is slow because the speech model downloads once.
- If Gemini shows 503 or 429 errors, wait a few minutes or change GEMINI_MODEL in `.env`.
- Never share your `.env` file or API key.