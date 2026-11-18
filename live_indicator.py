import streamlit.components.v1 as components

HTML = """
<div style="font-family:sans-serif;display:flex;align-items:center;gap:10px;">
  <div id="dot" style="width:18px;height:18px;border-radius:50%;background:#9e9e9e;"></div>
  <button id="btn" style="padding:4px 10px;">Start live indicator</button>
  <span id="msg" style="font-size:13px;color:#666;"></span>
</div>
<script>
const COOLDOWN_MS = 120000;   // at most one nudge every 2 minutes
const dot = document.getElementById('dot');
const btn = document.getElementById('btn');
const msg = document.getElementById('msg');
let lastNudge = 0, silenceStart = null, started = false;
let running = false, ctx, stream, timer;

function setColor(c) { dot.style.background = c; }
function nudge(text) {
  const now = Date.now();
  if (now - lastNudge < COOLDOWN_MS) return;
  lastNudge = now;
  msg.textContent = text;
  setTimeout(() => { msg.textContent = ''; }, 4000);
}
function stopAll() {
  clearInterval(timer);
  if (stream) stream.getTracks().forEach(t => t.stop());
  if (ctx) ctx.close();
  running = false; started = false; silenceStart = null;
  btn.textContent = 'Start live indicator';
  setColor('#9e9e9e');
}
btn.onclick = async () => {
  if (running) { stopAll(); return; }
  try {
    stream = await navigator.mediaDevices.getUserMedia({audio: true});
  } catch (e) {
    msg.textContent = 'Microphone not available here (' + e.name + ')';
    return;
  }
  ctx = new (window.AudioContext || window.webkitAudioContext)();
  const src = ctx.createMediaStreamSource(stream);
  const an = ctx.createAnalyser();
  an.fftSize = 1024;
  src.connect(an);
  const buf = new Float32Array(an.fftSize);
  running = true;
  btn.textContent = 'Stop live indicator';
  setColor('#2e7d32');
  timer = setInterval(() => {
    an.getFloatTimeDomainData(buf);
    let s = 0;
    for (const v of buf) s += v * v;
    const rms = Math.sqrt(s / buf.length);
    const now = Date.now();
    const speaking = rms > 0.015;
    if (speaking) { started = true; silenceStart = null; }
    else if (started && silenceStart === null) { silenceStart = now; }
    const silent = silenceStart ? (now - silenceStart) / 1000 : 0;
    if (silent >= 4) { setColor('#c62828'); nudge('Long silence'); }
    else if (silent >= 2 || (speaking && rms < 0.03)) { setColor('#f9a825'); }
    else { setColor('#2e7d32'); }
  }, 100);
};
</script>
"""


def render_indicator():
    components.html(HTML, height=60)