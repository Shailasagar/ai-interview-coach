import json
from analyzer import analyze_audio
from feedback import get_feedback
from resume_check import extract_resume_text, check_resume_match


def run_pipeline(audio_path, question, resume_path=None):
    voice = analyze_audio(audio_path)
    feedback = get_feedback(question, voice["transcript"])
    report = {"question": question, "voice": voice, "feedback": feedback}

    if resume_path:
        resume_text = extract_resume_text(resume_path)
        report["resume_check"] = check_resume_match(voice["transcript"], resume_text)

    return report


if __name__ == "__main__":
    report = run_pipeline("answer.mp3", "Tell me about yourself.", "resume.pdf")

    with open("report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("WPM:", report["voice"]["wpm"])
    print("Pauses:", len(report["voice"]["pauses"]))
    print("Feedback:", report["feedback"])
    print("Resume check:", report.get("resume_check"))