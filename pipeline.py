from datetime import datetime
from db import save_answer
import json
import time
from concurrent.futures import ThreadPoolExecutor
from analyzer import analyze_audio
from feedback import get_feedback
from resume_check import extract_resume_text, check_resume_match

try:
    from acoustics import analyze_acoustics
except Exception:
    analyze_acoustics = None


def safe_acoustics(audio_path):
    if analyze_acoustics is None:
        return None
    try:
        return analyze_acoustics(audio_path)
    except Exception as e:
        return {"error": str(e)[:80]}


def run_pipeline(audio_path, question, resume_path=None, session_id=None, mode="single"):
    t0 = time.time()
    voice = analyze_audio(audio_path)
    t1 = time.time()
    print(f"TIMING transcription: {t1 - t0:.1f}s")

    transcript = voice["transcript"]
    with ThreadPoolExecutor(max_workers=3) as pool:
        ac_future = pool.submit(safe_acoustics, audio_path)
        fb_future = pool.submit(get_feedback, question, transcript)
        rc_future = None
        if resume_path:
            resume_text = extract_resume_text(resume_path)
            rc_future = pool.submit(check_resume_match, transcript, resume_text)

        feedback = fb_future.result()
        resume_check = rc_future.result() if rc_future else None
        acoustics = ac_future.result()
    print(f"TIMING pitch/volume + gemini: {time.time() - t1:.1f}s")

    if acoustics is not None:
        voice["acoustics"] = acoustics

    report = {"question": question, "voice": voice, "feedback": feedback}
    if resume_check is not None:
        report["resume_check"] = resume_check
    try:
        save_answer(report, session_id or datetime.now().strftime("%Y%m%d-%H%M%S"), mode)
    except Exception as e:
        print("DB save failed:", str(e)[:80])
    return report


if __name__ == "__main__":
    report = run_pipeline("answer.mp3", "Tell me about yourself.", "resume.pdf")

    with open("report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("WPM:", report["voice"]["wpm"])
    print("Feedback:", report["feedback"])
    print("Resume check:", report.get("resume_check"))