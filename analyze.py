import whisper, re

model = whisper.load_model("base")
result = model.transcribe("answer.mp3")

text = result["text"]
words = text.split()
minutes = result["segments"][-1]["end"] / 60

print("Transcript:", text)
print("Words:", len(words))
print("WPM:", round(len(words) / minutes))

for f in ["um", "uh", "like", "you know"]:
    n = len(re.findall(rf"\b{f}\b", text.lower()))
    print(f, "->", n)