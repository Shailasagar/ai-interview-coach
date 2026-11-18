import re
import subprocess
import numpy as np

try:
    from faster_whisper import WhisperModel
    USE_FAST = True
except ImportError:
    import whisper
    USE_FAST = False

_model = None
FILLERS = ["um", "uh", "like", "you know", "apparently", "basically"]
SINGLE_FILLERS = {"um", "uh", "umm", "uhh", "like", "apparently", "basically"}


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
        words = [
            {"start": w.start, "end": w.end, "word": w.word}
            for s in segs for w in (s.words or [])
        ]
    else:
        result = model.transcribe(
            audio_path, word_timestamps=True, language="en", fp16=False
        )
        segs = result["segments"]
        text = result["text"].strip()
        end = segs[-1]["end"] if segs else 0
        words = [
            {"start": w["start"], "end": w["end"], "word": w["word"]}
            for s in segs for w in s.get("words", [])
        ]
    return text, end, words


def _clean(w):
    return re.sub(r"[^a-z']", "", w.lower())


def build_events(words, overall_wpm, pause_threshold=0.7):
    events, pauses = [], []

    for i in range(1, len(words)):
        gap = words[i]["start"] - words[i - 1]["end"]
        if gap >= pause_threshold:
            t = round(words[i - 1]["end"], 1)
            pauses.append({"at_seconds": t, "length_seconds": round(gap, 1)})
            events.append({"time_s": t, "type": "Long pause",
                           "detail": f"{gap:.1f}s of silence"})

    for i, w in enumerate(words):
        c = _clean(w["word"])
        if c in SINGLE_FILLERS:
            events.append({"time_s": round(w["start"], 1), "type": "Filler word",
                           "detail": f"'{c}'"})
        elif c == "you" and i + 1 < len(words) and _clean(words[i + 1]["word"]) == "know":
            events.append({"time_s": round(w["start"], 1), "type": "Filler word",
                           "detail": "'you know'"})

    if words:
        total = words[-1]["end"]
        t = 0.0
        while t < total:
            span = min(10.0, total - t)
            if span >= 5:
                n = sum(1 for w in words if t <= w["start"] < t + 10)
                win_wpm = round(n / (span / 60))
                if win_wpm > max(170, 1.4 * overall_wpm):
                    events.append({"time_s": round(t, 1), "type": "Pace spike",
                                   "detail": f"about {win_wpm} WPM in this 10s window"})
            t += 10.0

    events.sort(key=lambda e: e["time_s"])
    return events, pauses


def coaching_status(wpm, pauses, filler_total):
    longest = max((p["length_seconds"] for p in pauses), default=0)
    if (wpm and (wpm < 60 or wpm > 200)) or longest >= 3 or filler_total >= 8:
        return "red"
    if (wpm and (wpm < 90 or wpm > 170)) or len(pauses) >= 2 or filler_total >= 3:
        return "yellow"
    return "green"


def analyze_audio(audio_path, pause_threshold=0.7):
    text, end, words = _transcribe(audio_path)
    word_list = text.split()
    minutes = end / 60
    wpm = round(len(word_list) / minutes) if minutes else 0
    fillers = {f: len(re.findall(rf"\b{f}\b", text.lower())) for f in FILLERS}

    events, pauses = build_events(words, wpm, pause_threshold)
    status = coaching_status(wpm, pauses, sum(fillers.values()))

    return {
        "transcript": text,
        "word_count": len(word_list),
        "wpm": wpm,
        "fillers": fillers,
        "pauses": pauses,
        "events": events,
        "status": status,
    }