"""Sound design + mix for the Filare Brain cold open. Deterministic (seeded). Writes assets/audio/mix.wav (with VO)
and assets/audio/mix_novo.wav (music + SFX only), plus cues.json used by the cue sheet."""
import json, pathlib, subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 48000
LEN = 22.0
ROOT = pathlib.Path(__file__).resolve().parents[1]
VO = ROOT / "assets" / "vo" / "trim"
OUT = ROOT / "assets" / "audio"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)
N = int(SR * LEN)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=0.003, r=0.05):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lp(x, f, o=2):
    return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, hi], "band", fs=SR, output="sos"), x)


# ---------- sound effects ----------
def tick_slack():  # warm wooden knock, two quick partials
    d = t(0.09); x = (np.sin(2 * np.pi * 1180 * d) + 0.5 * np.sin(2 * np.pi * 1770 * d)) * np.exp(-d * 55)
    return 0.5 * x


def tick_mail():  # soft two-note glide, rounder
    d = t(0.22); f = np.where(d < 0.08, 740, 988)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-((d % 0.08 if False else d) * 14)) * env(len(d), 0.004, 0.08)
    return 0.4 * x


def tick_text():  # small bright bubble pluck
    d = t(0.07); x = np.sin(2 * np.pi * (2100 + 900 * np.exp(-d * 60)) * d) * np.exp(-d * 70)
    return 0.35 * x


def tick_discord():  # lower, muted blip
    d = t(0.08); x = np.sin(2 * np.pi * 620 * d) * np.exp(-d * 45)
    return 0.45 * lp(x, 2500)


def key_click():
    n = rng.standard_normal(int(0.018 * SR)) * np.exp(-t(0.018) * 260)
    return 0.25 * bp(n, 1800, 6000)


def ping():  # the precise notification that kicks the workday
    d = t(0.5); x = (np.sin(2 * np.pi * 1318.5 * d) + 0.35 * np.sin(2 * np.pi * 2637 * d)) * np.exp(-d * 9)
    return 0.32 * x * env(len(d), 0.002, 0.1)


def paper():
    n = rng.standard_normal(int(0.25 * SR)) * env(int(0.25 * SR), 0.02, 0.12)
    return 0.12 * bp(n, 1500, 7000)


def wind(d=1.7):
    n = rng.standard_normal(int(d * SR))
    x = lp(n, 420, 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t(d)))
    return 0.55 * x / np.max(np.abs(x)) * env(len(x), 0.15, 0.6)


def pulse(start=3.4, end=7.0):
    d = t(end - start); depth = np.linspace(0.25, 1.0, len(d)) ** 1.5
    rate = np.linspace(1.6, 2.6, len(d))
    beat = 0.5 * (1 + np.sin(2 * np.pi * np.cumsum(rate) / SR - np.pi / 2)) ** 3
    x = (np.sin(2 * np.pi * 52 * d) + 0.4 * np.sin(2 * np.pi * 104 * d)) * beat * depth
    x *= env(len(d), 0.3, 0.002)  # hard stop at the cut
    return 0.32 * x


def room(d=0.75):
    return 0.008 * lp(rng.standard_normal(int(d * SR)), 300) * env(int(d * SR), 0.01, 0.1)


def whoosh(d=0.55):
    n = rng.standard_normal(int(d * SR)); e = np.sin(np.pi * t(d) / d) ** 2
    return 0.10 * bp(n, 500, 3500) * e


def snap():  # small marker lock
    d = t(0.07); x = np.sin(2 * np.pi * 880 * d) * np.exp(-d * 80) + 0.6 * bp(rng.standard_normal(len(d)), 2000, 8000) * np.exp(-d * 200)
    return 0.32 * x


def lock():  # restrained mechanical lock: click + low thump
    d = t(0.25)
    click = bp(rng.standard_normal(len(d)), 2500, 9000) * np.exp(-d * 300)
    thump = np.sin(2 * np.pi * 95 * d) * np.exp(-d * 22)
    return 0.55 * (0.5 * click + thump)


def harmonic(d=6.0):  # one sustained resolving chord (A major, open voicing)
    tt = t(d); x = sum(a * np.sin(2 * np.pi * f * tt) for f, a in ((110, 1), (164.8, 0.6), (220, 0.5), (277.2, 0.3), (329.6, 0.25)))
    x *= env(len(tt), 0.35, 2.5) * (1 + 0.05 * np.sin(2 * np.pi * 0.4 * tt))
    return 0.08 * lp(x, 1800)


def thunk():  # the draft stopping at the boundary
    d = t(0.3); x = np.sin(2 * np.pi * (78 + 40 * np.exp(-d * 30)) * d) * np.exp(-d * 18)
    return 0.5 * x + 0.15 * bp(rng.standard_normal(len(d)), 1500, 6000) * np.exp(-d * 250)


def chime():  # waiting-on-Paolo status settles
    d = t(0.6); x = (np.sin(2 * np.pi * 659.3 * d) + 0.5 * np.sin(2 * np.pi * 987.8 * d)) * np.exp(-d * 6)
    return 0.12 * x * env(len(d), 0.01, 0.2)


SFX = [  # (time, name, fn, gain, pan -1..1)
    (0.00, "wind", wind, 1.0, 0.0),
    (1.02, "notification", ping, 1.0, 0.0),
    (1.10, "slack (Davide)", tick_slack, 1.0, -0.2),
    (2.02, "email (Stefano)", tick_mail, 1.0, 0.2),
]
SFX += [(2.92 + i * 0.075, "typing (Paolo draft)", key_click, 0.8, 0.0) for i in range(6)]
SFX += [
    (3.40, "pulse under pileup", lambda: pulse(3.4, 7.0), 1.0, 0.0),
    (3.58, "slack (Sara)", tick_slack, 0.9, -0.25),
    (4.05, "slack reply", tick_slack, 0.7, -0.1),
    (4.10, "discord (Marco)", tick_discord, 0.9, 0.3),
    (4.48, "text (Marta)", tick_text, 0.9, 0.25),
    (4.75, "drive doc (Luca)", paper, 1.0, -0.1),
    (5.28, "slack DM (Elena)", tick_slack, 0.9, 0.0),
    (5.90, "text (Stefano follow-up)", tick_text, 1.0, -0.2),
]
for i, tt in enumerate([6.12, 6.24, 6.33, 6.45, 6.52, 6.61, 6.68, 6.74, 6.81, 6.86, 6.91, 6.95]):
    SFX.append((tt, "notification pile", [tick_slack, tick_text, tick_mail, tick_discord][i % 4], 0.45 + 0.03 * i, [-0.3, 0.3, -0.1, 0.2][i % 4]))
SFX += [
    (7.00, "room tone (silence)", lambda: room(0.75), 1.0, 0.0),
    (7.70, "fragments travel", lambda: whoosh(0.6), 1.0, 0.0),
    (8.75, "normalize to timeline", lambda: whoosh(0.5), 0.8, 0.0),
    (9.40, "Wed marker locks", snap, 1.0, -0.15),
    (10.20, "Thu marker locks", snap, 1.0, 0.15),
    (10.90, "path reaches Thursday: lock", lock, 1.0, 0.0),
    (10.95, "resolving harmonic", lambda: harmonic(6.5), 1.0, 0.0),
    (14.05, "draft held at boundary", thunk, 1.0, 0.0),
    (16.15, "internal path opens", lambda: whoosh(0.5), 0.7, 0.1),
    (17.00, "waiting on Paolo", chime, 1.0, 0.0),
    (18.80, "mock outbox empty", chime, 0.5, 0.0),
]

# ---------- dialogue ----------
# (start, id, speaker, line, gain, tempo, pan, lowpass_hz)
VOICES = [
    (1.10, "davide", "Davide", "Thursday. Seven a.m.", 1.0, 1.12, -0.1, None),
    (2.05, "stefano", "Stefano", "Frost Wednesday night.", 1.0, 1.10, 0.1, None),
    (2.95, "paolo", "Paolo", "I've got Thursday in the reply.", 0.95, 1.15, 0.0, None),
    (3.60, "sara", "Sara", "Forty are still offline.", 0.42, 1.15, -0.3, None),
    (4.10, "marco", "Marco", "I'm checking the spare.", 0.40, 1.10, 0.3, None),
    (4.50, "marta", "Marta", "No earlier slot confirmed.", 0.40, 1.15, 0.25, 3200),
    (4.95, "luca", "Luca", "That's the old sheet.", 0.26, 1.10, -0.25, 2600),
    (5.30, "elena", "Elena", "What can we actually tell them?", 0.85, 1.10, 0.0, None),
    (5.92, "stefano2", "Stefano (text follow-up)", "Can someone confirm?", 0.80, 1.12, 0.1, None),
    (7.70, "brain1a", "Filare Brain", "I found the conflict.", 1.0, 1.0, 0.0, None),
    (9.30, "brain1b", "Filare Brain", "They need coverage Wednesday night.", 1.0, 1.0, 0.0, None),
    (11.05, "brain1c", "Filare Brain", "The repair is scheduled for Thursday morning.", 1.0, 1.0, 0.0, None),
    (13.55, "brain2a", "Filare Brain", "I've held the customer reply.", 1.0, 1.0, 0.0, None),
    (15.35, "brain2b", "Filare Brain", "Paolo, ask Davide whether we can get there sooner.", 1.0, 1.0, 0.0, None),
]


def load_voice(vid, tempo, lpf):
    src = VO / f"{vid}.wav"
    tmp = OUT / f"_{vid}.wav"
    af = [f"atempo={tempo}"] if tempo != 1.0 else ["anull"]
    if lpf:
        af.append(f"lowpass=f={lpf}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", ",".join(af), "-ar", str(SR), "-ac", "1", str(tmp)], check=True)
    sr, x = wavfile.read(tmp); tmp.unlink()
    x = x.astype(np.float64) / 32768.0
    return x


def place(bus, x, start, gain, pan):
    i = int(start * SR); x = x[: max(0, N - i)] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    bus[0, i:i + len(x)] += x * l * 1.414 * 0.707 / 0.707 * 0.707
    bus[1, i:i + len(x)] += x * r * 1.414 * 0.707 / 0.707 * 0.707


fx = np.zeros((2, N)); vo = np.zeros((2, N)); cues = []
for st, name, fn, g, p in SFX:
    place(fx, fn(), st, g, p); cues.append({"t": st, "kind": "sfx", "what": name})

vo_env = np.zeros(N)
for st, vid, spk, line, g, tempo, p, lpf in VOICES:
    x = load_voice(vid, tempo, lpf)
    # normalise each line to a common peak before the gain
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.5
    place(vo, x, st, g, p)
    end = st + len(x) / SR
    cues.append({"t": st, "end": round(end, 2), "kind": "vo", "speaker": spk, "line": line})
    if spk == "Filare Brain" or g >= 0.8:
        vo_env[int(st * SR):int(end * SR)] = 1.0

# hard cut of chatter at 7.00 (the silence beat)
cut = int(7.0 * SR); fade = int(0.012 * SR)
vo[:, cut - fade:cut] *= np.linspace(1, 0, fade); vo[:, cut:int(7.65 * SR)] = 0

# duck SFX under foreground voices (smoothed)
k = int(0.08 * SR); duck = np.convolve(vo_env, np.ones(k) / k, mode="same")
fx_ducked = fx * (1 - 0.45 * duck)


def finish(x, path):
    pk = np.max(np.abs(x)); x = x / pk * 0.89  # ~ -1 dBFS peak
    wavfile.write(path, SR, (x.T * 32767).astype(np.int16))


finish(fx_ducked + vo, OUT / "mix.wav")
finish(fx, OUT / "mix_novo.wav")
mono = (fx_ducked + vo).mean(axis=0)
finish(np.vstack([mono, mono]), OUT / "mix_mono_check.wav")
(OUT / "cues.json").write_text(json.dumps(sorted(cues, key=lambda c: c["t"]), indent=1))
print("ok", {c["speaker"]: (c["t"], c["end"]) for c in cues if c["kind"] == "vo"})
