import subprocess
import numpy as np
import re

try:
    from faster_whisper import WhisperModel
    USE_FAST = True
except ImportError:
    import whisper
    USE_FAST = False

_model = None
FILLERS = ["um", "uh", "like", "you know", "apparently", "basically"]


def get_model():
    global _model
    if _model is None:
        if USE_FAST:
            _model = WhisperModel("base.en", device="cpu", compute_type="int8")
        else:
            _model = whisper.load_model("base.en")
    return _model
def load_audio(path):
    cmd = ["ffmpeg", "-nostdin", "-i", path,
           "-f", "s16le", "-ac", "1", "-ar", "16000", "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16).astype(np.float32) / 32768.0


def _transcribe(audio_path):
    model = get_model()
    if USE_FAST:
        segs, _ = model.transcribe(
            load_audio(audio_path), language="en", word_timestamps=True, beam_size=1
        )
        segs = list(segs)
        text = " ".join(s.text.strip() for s in segs).strip()
        end = segs[-1].end if segs else 0
        words = [(w.start, w.end) for s in segs for w in (s.words or [])]
    else:
        result = model.transcribe(
            audio_path, word_timestamps=True, language="en", fp16=False
        )
        segs = result["segments"]
        text = result["text"].strip()
        end = segs[-1]["end"] if segs else 0
        words = [(w["start"], w["end"]) for s in segs for w in s.get("words", [])]
    return text, end, words


def analyze_audio(audio_path, pause_threshold=0.7):
    text, end, words = _transcribe(audio_path)
    word_list = text.split()
    minutes = end / 60
    wpm = round(len(word_list) / minutes) if minutes else 0
    fillers = {f: len(re.findall(rf"\b{f}\b", text.lower())) for f in FILLERS}

    pauses = []
    for i in range(1, len(words)):
        gap = words[i][0] - words[i - 1][1]
        if gap >= pause_threshold:
            pauses.append({
                "at_seconds": round(words[i - 1][1], 1),
                "length_seconds": round(gap, 1),
            })

    return {
        "transcript": text,
        "word_count": len(word_list),
        "wpm": wpm,
        "fillers": fillers,
        "pauses": pauses,
    }