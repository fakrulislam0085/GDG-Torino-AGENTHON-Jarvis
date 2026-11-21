# Jarvis film: cue sheet

- **Film:** `out/jarvis-film.mp4`. 1920×1080, 30 fps, H.264 + AAC, **21.00 s** (hard cap 21), about −16 LUFS, −1.5 dBTP peak.
- **Clean (no voice, keeps UI ticks and the closing tone):** `out/jarvis-film_clean-no-voice.mp4`.
- **Audio:** voiced with ElevenLabs stock voice **Daniel** (`onwK4e9ZLuTAKqWW03F9`, eleven_multilingual_v2), 3 lines. The SFX are synthesized in `tools/mix.py`.
- **Presenter cut point:** the final frame (orb + closing line + credit + caption) is complete at **0:19.45**. It holds to **0:20.97**.
- **Data:** `jarvis-your-company-brain/data_ariete`, updated demo date **Sat 21 Nov 2026**.

## Picture

| Time | Beat |
|---|---|
| 0:00.0–0:02.9 | Cover. The orb fades up (35% opacity at frame 0). "Jarvis." at 0.55, teal line "The colleague who knows, speaks first, and asks before it acts." at 1.0. Caption: Fictional scenario built on Ariete Tech Solutions' public services. Not Ariete's data. |
| 0:03.05–0:06.3 | Kicker SAT 21 NOV · 08:00 · NOBODY ASKED. "Good morning, Francesca." / Saturday 21 November. Three rows: Rinaldi PEC attachments, 18 files since 16 Nov `mem-003` · EuroGPU CLD-2026-0412 EUR 3,660 due Sun 22 Nov, second notice `mem-005` · "Action needed" flagged, not acted on `email-008` |
| 0:06.3 | SAT 21 NOV · 09:05 · AN URGENT EMAIL. `email-011` from Roberto Rinaldi to Silvia Ferraris, cc Lorenzo Bertola: "URGENT: document intake stopped, 60 client files stuck" · stopped Wednesday night · deadline 28 November |
| 0:06.55 | Amber flag: FLAGGED URGENT · 60 client files stuck · deadline 28 Nov |
| 0:06.7 | Call card "Jarvis → Francesca" rings. The orb moves into it and pulses with the voice. Captions at 7.3 and 9.0 |
| 0:12.3–0:12.55 | ASKS BEFORE IT ACTS: "Fix message to Lorenzo" and "Zoom with Lorenzo", both WAITING FOR YOUR TAP (amber). "Nothing happens until Francesca taps Approve in the app." at 13.1 |
| 0:15.4 | BLOCKED (red): a fake CEO email asking Marta to wire EUR 9,800 today |
| 0:17.55 / 0:17.85 | Taps on Approve. APPROVED BY FRANCESCA (green) at 17.73 and 18.03 |
| 0:18.55–0:19.45 | Close: orb centre, teal "A colleague you trust says \"I don't know\", and \"May I?\"", Token Mafia · AGENTHON, caption |

## Voice (Jarvis)

| Start | End | Line |
|---|---|---|
| 3.30 | 6.27 | "Good morning, Francesca. Here's what needs you today." |
| 7.30 | 14.79 | "Francesca, this is Jarvis. Studio Rinaldi's document intake has stopped, and sixty client files are stuck before the tax deadline." |
| 14.95 | 17.57 | "The fix is ready. I'll wait for your yes." |

The call line runs at 1.04× with the pauses between sentences shortened. No other processing.

## Sound effects

| Time | Effect |
|---|---|
| 0.40 | orb fades up |
| 3.05 | brief card |
| 3.70 | brief row |
| 3.95 | brief row |
| 4.20 | brief row |
| 6.30 | email arrives |
| 6.55 | flagged urgent |
| 6.72 | phone rings |
| 12.30 | fix message card |
| 12.55 | zoom card |
| 15.40 | fake CEO email blocked |
| 17.70 | tap approve (fix) |
| 17.75 | approved |
| 18.00 | tap approve (zoom) |
| 18.05 | approved |
| 18.60 | close tone |

## Facts checked against data_ariete (Sat 21 Nov 2026)
- **People:** Francesca Morello (CEO), Marta Ghiglione (CFO), Silvia Ferraris (Account manager), Lorenzo Bertola (Automation engineer).
- **email-011:** sent 09:05, from roberto@studiorinaldi.example to Silvia, cc Lorenzo. The subject is verbatim. It stopped Wednesday night; 60 files; deadline 28 November.
- **mem-003:** 18 files since 16 Nov.
- **mem-005:** EUR 3,660, due Sun 22 Nov, second notice.
- **email-008:** "Action needed".
- **Fake CEO example:** EUR 9,800 wire to Marta.
- The film invents no numbers or results and shows no logos.
- **Zoom card:** no meeting time is shown; the card says it is created only after approval, as in `brain/call.py`.
