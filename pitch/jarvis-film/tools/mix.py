"""Calm sound design + mix for the Jarvis film. Writes assets/audio/mix.wav, mix_novo.wav, cues.json."""
import json, pathlib, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 48000
LEN = float(sys.argv[1]) if len(sys.argv) > 1 else 20.5
ROOT = pathlib.Path(__file__).resolve().parents[1]
VO = ROOT / "assets" / "vo" / "trim"
OUT = ROOT / "assets" / "audio"; OUT.mkdir(parents=True, exist_ok=True)
N = int(SR * LEN); rng = np.random.default_rng(11)


def t(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.004, r=0.05):
    e = np.ones(n); na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def lp(x, f): return sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)


def tick():  # soft UI tick
    d = t(0.06); return 0.22 * np.sin(2 * np.pi * 1500 * d) * np.exp(-d * 90)
def soft_in():  # card arrives: tiny airy swell + tick
    d = t(0.3); n = bp(rng.standard_normal(len(d)), 1200, 5000) * np.sin(np.pi * d / 0.3) ** 2
    tk = np.zeros(len(d)); s = tick(); i0 = int(0.22 * SR); tk[i0:i0 + len(s)] = s[: len(d) - i0]
    return 0.05 * n + tk
def flag():  # urgent flag: two soft rising notes
    d = t(0.32); f = np.where(d < 0.14, 784, 1046.5)
    return 0.16 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-(d % 0.14) * 12) * env(len(d), 0.003, 0.06)
def ring():  # gentle phone ring burst (440+480 Hz, soft)
    d = t(0.55); x = (np.sin(2 * np.pi * 440 * d) + np.sin(2 * np.pi * 480 * d)) * (0.5 + 0.5 * np.sin(2 * np.pi * 18 * d))
    return 0.07 * x * env(len(d), 0.03, 0.12)
def tap():
    d = t(0.08); return 0.3 * (np.sin(2 * np.pi * 900 * d) * np.exp(-d * 70) + 0.4 * bp(rng.standard_normal(len(d)), 2000, 7000) * np.exp(-d * 200))
def approved():  # small confirming major third
    d = t(0.5); x = np.sin(2 * np.pi * 659.3 * d) + 0.7 * np.sin(2 * np.pi * 830.6 * np.clip(d - 0.07, 0, None)) * (d > 0.07)
    return 0.12 * x * np.exp(-d * 5) * env(len(d), 0.004, 0.15)
def blocked():  # muted low double knock
    d = t(0.22); x = np.sin(2 * np.pi * 220 * d) * (np.exp(-d * 40) + 0.8 * np.exp(-np.clip(d - 0.1, 0, None) * 40) * (d > 0.1))
    return 0.16 * lp(x, 1500)
def tone(d=3.2):  # one soft tone under the close
    tt = t(d); x = sum(a * np.sin(2 * np.pi * f * tt) for f, a in ((146.8, 1), (220, 0.55), (293.7, 0.35), (370, 0.2)))
    return 0.05 * x * env(len(tt), 0.6, 1.6)
def bed(d):  # very light air under the whole film
    return 0.006 * lp(rng.standard_normal(int(d * SR)), 900) * env(int(d * SR), 0.8, 1.0)


def shrink_pauses(x, thr=0.012, keep=0.14, minlen=0.2):
    a = np.abs(x); k = int(0.02 * SR); sm = np.convolve(a, np.ones(k) / k, "same"); quiet = sm < thr
    out, i, n = [], 0, len(x)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]: j += 1
            seg = x[i:j]
            if (j - i) / SR > minlen and i > 0 and j < n:
                h = int(keep * SR / 2); seg = np.concatenate([seg[:h], seg[-h:]])
            out.append(seg); i = j
        else:
            j = i
            while j < n and not quiet[j]: j += 1
            out.append(x[i:j]); i = j
    return np.concatenate(out)


def voice(vid, tempo=1.0, shrink=False):
    tmp = OUT / f"_{vid}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(VO / f"{vid}.wav"), "-af", f"atempo={tempo}" if tempo != 1 else "anull",
                    "-ar", str(SR), "-ac", "1", str(tmp)], check=True)
    _, x = wavfile.read(tmp); tmp.unlink(); x = x.astype(np.float64) / 32768
    if shrink: x = shrink_pauses(x)
    return x / (np.max(np.abs(x)) + 1e-9) * 0.5


T = json.loads((ROOT / "tools" / "timing.json").read_text())  # the edit's timing, shared with the composition
fx = np.zeros(N); vo = np.zeros(N); cues = []
def put(bus, x, at, g=1.0):
    i = int(at * SR); x = x[: max(0, N - i)] * g; bus[i:i + len(x)] += x

for at, name, fn, g in T["sfx"]:
    put(fx, {"tick": tick, "in": soft_in, "flag": flag, "ring": ring, "tap": tap, "approved": approved,
             "blocked": blocked, "tone": tone}[fn](), at, g); cues.append({"t": at, "kind": "sfx", "what": name})
put(fx, bed(LEN), 0)
vo_env = np.zeros(N)
for v in T["vo"]:
    x = voice(v["id"], v.get("tempo", 1.0), v.get("shrink", False)); put(vo, x, v["at"]); end = v["at"] + len(x) / SR
    vo_env[int(v["at"] * SR):int(end * SR)] = 1
    cues.append({"t": v["at"], "end": round(end, 2), "kind": "vo", "speaker": "Jarvis", "line": v["line"]})
k = int(0.1 * SR); duck = np.convolve(vo_env, np.ones(k) / k, "same")
mix = fx * (1 - 0.35 * duck) + vo


def write(x, p):
    x = x / np.max(np.abs(x)) * 0.89; wavfile.write(p, SR, (np.vstack([x, x]).T * 32767).astype(np.int16))
write(mix, OUT / "mix_raw.wav"); write(fx, OUT / "mix_novo_raw.wav")
for a, b in (("mix_raw", "mix"), ("mix_novo_raw", "mix_novo")):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / f"{a}.wav"), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", str(OUT / f"{b}.wav")], check=True)
# voice envelope for the orb pulse (20 fps RMS), so the orb moves with the words
hop = SR // 20; rms = [float(np.sqrt(np.mean(vo[i:i + hop] ** 2))) for i in range(0, N, hop)]
m = max(rms) or 1; (ROOT / "assets" / "audio" / "voice_env.json").write_text(json.dumps([round(r / m, 3) for r in rms]))
(OUT / "cues.json").write_text(json.dumps(sorted(cues, key=lambda c: c["t"]), indent=1))
print({c["line"][:30]: (c["t"], c["end"]) for c in cues if c["kind"] == "vo"})
