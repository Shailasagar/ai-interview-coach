import json
from analyzer import analyze_audio
from feedback import get_feedback

def run_pipeline(audio_path, question):
    voice = analyze_audio(audio_path)
    feedback = get_feedback(question, voice["transcript"])
    return {"question": question, "voice": voice, "feedback": feedback}

if __name__ == "__main__":
    report = run_pipeline("answer.mp3", "Tell me about yourself.")

    with open("report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("Transcript:", report["voice"]["transcript"])
    print("WPM:", report["voice"]["wpm"])
    print("Fillers:", report["voice"]["fillers"])
    print("Pauses:", report["voice"]["pauses"])
    print("Feedback:", report["feedback"])