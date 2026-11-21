"""Render each spoken line with ElevenLabs stock voices. Reads the key from a git-ignored .env; never prints it."""
import json, os, pathlib, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "vo"
OUT.mkdir(parents=True, exist_ok=True)
REPO = ROOT.parents[1]


def key():
    for p in (REPO / "builds" / "best" / ".env", REPO / "builds" / "arif" / ".env"):
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith("ELEVENLABS_API_KEY="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    sys.exit("no ElevenLabs key found")


# id, voice_id (ElevenLabs premade/stock), text, stability, style
LINES = [
    ("davide", "nPczCjzI2devNBz1zQrb", "Thursday. Seven a.m.", 0.55, 0.15),          # Brian
    ("stefano", "pqHfZKP75CvOlQylNhV4", "Frost Wednesday night.", 0.45, 0.30),       # Bill
    ("paolo", "TX3LPaxmHKxFdv7VOQHJ", "I've got Thursday in the reply.", 0.35, 0.35),  # Liam
    ("sara", "XrExE9yKIg1WjnnlVkGX", "Forty are still offline.", 0.5, 0.1),          # Matilda
    ("marco", "iP95p4xoKVk53GoZ742B", "I'm checking the spare.", 0.45, 0.2),         # Chris
    ("marta", "FGY2WhTYpPnrIDTdsKH5", "No earlier slot confirmed.", 0.45, 0.2),      # Laura
    ("luca", "cjVigY5qzO86Huf0OWal", "That's the old sheet.", 0.45, 0.2),            # Eric
    ("elena", "Xb7hH8MSUJpSbSDYk0k2", "What can we actually tell them?", 0.4, 0.35),  # Alice
    ("stefano2", "pqHfZKP75CvOlQylNhV4", "Can someone confirm?", 0.4, 0.35),         # Bill
    ("brain1a", "onwK4e9ZLuTAKqWW03F9", "I found the conflict.", 0.7, 0.0),          # Daniel
    ("brain1b", "onwK4e9ZLuTAKqWW03F9", "They need coverage Wednesday night.", 0.7, 0.0),
    ("brain1c", "onwK4e9ZLuTAKqWW03F9", "The repair is scheduled for Thursday morning.", 0.7, 0.0),
    ("brain2a", "onwK4e9ZLuTAKqWW03F9", "I've held the customer reply.", 0.7, 0.0),
    ("brain2b", "onwK4e9ZLuTAKqWW03F9", "Paolo, ask Davide whether we can get there sooner.", 0.7, 0.0),
    ("sol1", "onwK4e9ZLuTAKqWW03F9", "This is Jarvis.", 0.7, 0.05),
    ("sol2", "onwK4e9ZLuTAKqWW03F9", "An autonomous colleague that watches your team's email, chat and documents, connects the evidence, and asks before it acts.", 0.6, 0.05),
]


def tts(k, vid, text, stab, style, dst):
    body = json.dumps({
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": stab, "similarity_boost": 0.8, "style": style, "use_speaker_boost": True},
    }).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
        data=body, headers={"xi-api-key": k, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=60) as r:
        dst.write_bytes(r.read())


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).decode().strip())


if __name__ == "__main__":
    k = key()
    only = set(sys.argv[1:])
    out = {}
    for lid, vid, text, stab, style in LINES:
        dst = OUT / f"{lid}.mp3"
        if (not only and not dst.exists()) or lid in only:
            try:
                tts(k, vid, text, stab, style, dst)
            except Exception as e:  # report without the key
                print(f"{lid}: FAILED {type(e).__name__}: {getattr(e, 'code', '')} {str(e)[:120]}")
                continue
        out[lid] = round(dur(dst), 3)
        print(f"{lid}: {out[lid]}s  {text}")
    (OUT / "durations.json").write_text(json.dumps(out, indent=1))
