import numpy as np
import librosa


def analyze_acoustics(audio_path):
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    if len(y) < sr:  # shorter than 1 second
        return {"error": "Audio too short to analyze."}

    # ---------- Volume (RMS energy in dB) ----------
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
    db = 20 * np.log10(rms + 1e-6)
    speech = rms > 0.1 * np.percentile(rms, 95)  # ignore silence
    speech_db = db[speech]

    volume_std = float(np.std(speech_db)) if len(speech_db) else 0.0
    trailing_drop = 0.0
    if len(speech_db) >= 20:
        cut = int(len(speech_db) * 0.8)
        trailing_drop = float(np.mean(speech_db[:cut]) - np.mean(speech_db[cut:]))

    # ---------- Pitch (F0 with pYIN) ----------
    f0, voiced, _ = librosa.pyin(
        y, fmin=65, fmax=400, sr=sr, frame_length=1024
    )
    f0 = f0[~np.isnan(f0)]
    if len(f0) > 20:
        semitones = 12 * np.log2(f0 / np.median(f0))
        pitch_std = float(np.std(semitones))
        pitch_median = float(np.median(f0))
    else:
        pitch_std, pitch_median = None, None

    if pitch_std is None:
        pitch_note = "Not enough voiced speech to estimate pitch."
    elif pitch_std < 1.5:
        pitch_note = "Pitch varied little, which may sound flat. Try stressing key words."
    elif pitch_std > 4.5:
        pitch_note = "Pitch varied a lot, which sounds expressive."
    else:
        pitch_note = "Pitch variation was in a typical range."

    if volume_std > 8:
        volume_note = "Your volume changed a lot during the answer."
    else:
        volume_note = "Your volume was fairly consistent."

    if trailing_drop >= 6:
        volume_note += " It dropped noticeably near the end, so try to finish with a strong voice."

    return {
        "pitch_median_hz": round(pitch_median, 1) if pitch_median else None,
        "pitch_variation_semitones": round(pitch_std, 2) if pitch_std is not None else None,
        "pitch_note": pitch_note,
        "volume_variation_db": round(volume_std, 1),
        "trailing_off_db": round(trailing_drop, 1),
        "volume_note": volume_note,
    }