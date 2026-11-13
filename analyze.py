import whisper, re

model = whisper.load_model("base")
result = model.transcribe("answer.mp3", word_timestamps=True)

text = result["text"]
words = text.split()
minutes = result["segments"][-1]["end"] / 60

print("Transcript:", text)
print("Words:", len(words))
print("WPM:", round(len(words) / minutes))

for f in ["um", "uh", "like", "you know"]:
    n = len(re.findall(rf"\b{f}\b", text.lower()))
    print(f, "->", n)

# Pause detection
all_words = []
for seg in result["segments"]:
    all_words.extend(seg["words"])

pauses = []
for i in range(1, len(all_words)):
    gap = all_words[i]["start"] - all_words[i - 1]["end"]
    if gap >= 0.7:  # pauses of 0.7 seconds or more
        pauses.append((round(all_words[i - 1]["end"], 1), round(gap, 1)))

print("Pauses (0.7s or longer):", len(pauses))
for time, length in pauses:
    print(f"  at {time}s -> {length}s pause")   
with open("transcript.txt", "w", encoding="utf-8") as f:
    f.write(text)