# Filare Brain cold open: cue sheet

- **Master:** `out/filare-brain-cold-open.mp4`. 1920×1080, 30 fps, H.264 + AAC, **22.00 s**, about −17 LUFS integrated, −1.3 dBTP peak.
- **Clean (no voice, keeps SFX and sound bed):** `out/filare-brain-cold-open_clean-no-voice.mp4`. **Silent picture:** `out/filare-brain-cold-open_silent.mp4`.
- **Audio:** voiced with ElevenLabs stock voices (eleven_multilingual_v2), one file per line in `assets/vo/`. The SFX and sound bed are synthesized in `tools/mix.py`.
- **Presenter cut point:** the final frame is fully built at **0:18.80**. Hold until **0:21.97**, the last frame, or cut any time after 0:19.5 into Paolo's Approvals view: *"Here's the actual draft. Watch what happens when I try to approve it."*
- **Source:** `index.html` + `compositions/film.html` (HyperFrames). Rebuild the audio with `python tools/mix.py`, then render with the HyperFrames CLI.

## Picture

| Time | Beat |
|---|---|
| 0:00.0–0:01.1 | Vineyard at dusk, GW-07 light dies. LANGHE VIVA / 40 SENSORS OFFLINE. Caption: Dramatized synthetic scenario |
| 0:01.1 | Davide, Slack #field-ops: "GW-07 rollout. Thu 26 Nov, 07:00." (the time token flashes at 1.45) |
| 0:02.0 | Stefano, email: "Frost forecast tomorrow night — Wed 25 Nov. Can you confirm coverage?" |
| 0:02.9 | Paolo's draft: "We're scheduled to roll out the fix on Thursday at 07:00." UNSENT · AWAITING APPROVAL, cursor blinking |
| 0:03.5–0:07.0 | Pile-up with a slow push. Sara 3.58, Slack reply 4.05, Marco 4.10, Marta 4.48, Drive "old copy" 4.75, Elena 5.28, Stefano text 5.90, echoes 6.0, heroes WEDNESDAY NIGHT 6.08 / THURSDAY · 07:00 6.25, draft refocus 6.5 |
| 0:07.0–0:07.65 | Hard audio cut. The frame freezes, support cards dim and recede, the draft shrinks to a silhouette |
| 0:07.75 | Case anchor LANGHE VIVA · GW-07. Both fragments pass it, keeping their source labels |
| 0:08.75 | Axis draws. **Wed marker locks 9.40**, **Thu marker locks 10.20** |
| 0:10.30–0:10.90 | Path draws Wed → Thu, mechanical lock at 10.90 |
| 0:11.25 | Verdict: "The repair is scheduled after the frost." |
| 0:13.2 | Timeline moves up. The draft returns, slides to the send boundary and **stops at 14.05: HELD FOR REVIEW · Original draft kept** |
| 0:16.15–0:17.0 | Teal path → INTERNAL REQUEST TO DAVIDE · **WAITING ON PAOLO** · Ask about an earlier fix or a spare gateway |
| 0:18.4–0:18.8 | FILARE BRAIN mark, caption, **MOCK OUTBOX · EMPTY**. Hold to the end |

## Dialogue (as placed in the mix)

| Start | End | Speaker | Line |
|---|---|---|---|
| 1.10 | 2.14 | Davide | "Thursday. Seven a.m." |
| 2.05 | 3.05 | Stefano | "Frost Wednesday night." |
| 2.95 | 4.29 | Paolo | "I've got Thursday in the reply." |
| 3.60 | 4.76 | Sara | "Forty are still offline." |
| 4.10 | 4.98 | Marco | "I'm checking the spare." |
| 4.50 | 5.86 | Marta | "No earlier slot confirmed." |
| 4.95 | 5.69 | Luca | "That's the old sheet." |
| 5.30 | 6.56 | Elena | "What can we actually tell them?" |
| 5.92 | 6.93 | Stefano (text follow-up) | "Can someone confirm?" |
| 7.70 | 9.10 | Filare Brain | "I found the conflict." |
| 9.30 | 10.89 | Filare Brain | "They need coverage Wednesday night." |
| 11.05 | 13.30 | Filare Brain | "The repair is scheduled for Thursday morning." |
| 13.55 | 15.12 | Filare Brain | "I've held the customer reply." |
| 15.35 | 18.61 | Filare Brain | "Paolo, ask Davide whether we can get there sooner." |

Chaos lines are sped up 1.10–1.15× and trimmed so they overlap. Secondary voices sit lower and slightly off-centre (pan ≤ 0.3). Marta and Luca are low-passed to sound farther away. All voice is cut hard at 7.00.
Voices: Davide = Brian · Stefano = Bill · Paolo = Liam · Sara = Matilda · Marco = Chris · Marta = Laura · Luca = Eric · Elena = Alice · Filare Brain = Daniel.

## Sound effects

| Time | Effect |
|---|---|
| 0.00 | wind |
| 1.02 | notification |
| 1.10 | slack (Davide) |
| 2.02 | email (Stefano) |
| 2.92 | typing (Paolo draft) |
| 3.00 | typing (Paolo draft) |
| 3.07 | typing (Paolo draft) |
| 3.15 | typing (Paolo draft) |
| 3.22 | typing (Paolo draft) |
| 3.29 | typing (Paolo draft) |
| 3.40 | pulse under pileup |
| 3.58 | slack (Sara) |
| 4.05 | slack reply |
| 4.10 | discord (Marco) |
| 4.48 | text (Marta) |
| 4.75 | drive doc (Luca) |
| 5.28 | slack DM (Elena) |
| 5.90 | text (Stefano follow-up) |
| 6.12 | notification pile |
| 6.24 | notification pile |
| 6.33 | notification pile |
| 6.45 | notification pile |
| 6.52 | notification pile |
| 6.61 | notification pile |
| 6.68 | notification pile |
| 6.74 | notification pile |
| 6.81 | notification pile |
| 6.86 | notification pile |
| 6.91 | notification pile |
| 6.95 | notification pile |
| 7.00 | room tone (silence) |
| 7.70 | fragments travel |
| 8.75 | normalize to timeline |
| 9.40 | Wed marker locks |
| 10.20 | Thu marker locks |
| 10.90 | path reaches Thursday: lock |
| 10.95 | resolving harmonic |
| 14.05 | draft held at boundary |
| 16.15 | internal path opens |
| 17.00 | waiting on Paolo |
| 18.80 | mock outbox empty |

## Facts checked on screen
- 40 sensors and GW-07.
- Wed 25 Nov is shown as a night window, with no invented hour. The rollout is Thu 26 Nov 07:00 and stays unchanged.
- The customer reply is unsent and held, with the original draft kept.
- The internal request is to Davide, with Paolo as the approver. Its state is waiting, not approved.
- The mock outbox is empty.
- An earlier fix is only asked about, never promised.
- "Dramatized synthetic scenario" shows at 0:00.2–0:01.1 and 0:18.4–end.
- Slack, Discord, texts and Drive appear only as dramatized sources.
