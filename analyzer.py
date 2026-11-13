import re
import whisper

_model = None

def get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model

FILLERS = ["um", "uh", "like", "you know"]

def analyze_audio(audio_path, pause_threshold=0.7):
    result = get_model().transcribe(audio_path, word_timestamps=True)

    text = result["text"].strip()
    words = text.split()
    segments = result["segments"]
    minutes = segments[-1]["end"] / 60 if segments else 0
    wpm = round(len(words) / minutes) if minutes else 0

    fillers = {
        f: len(re.findall(rf"\b{f}\b", text.lower())) for f in FILLERS
    }

    all_words = []
    for seg in segments:
        all_words.extend(seg.get("words", []))

    pauses = []
    for i in range(1, len(all_words)):
        gap = all_words[i]["start"] - all_words[i - 1]["end"]
        if gap >= pause_threshold:
            pauses.append({
                "at_seconds": round(all_words[i - 1]["end"], 1),
                "length_seconds": round(gap, 1),
            })

    return {
        "transcript": text,
        "word_count": len(words),
        "wpm": wpm,
        "fillers": fillers,
        "pauses": pauses,
    }