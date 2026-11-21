# Company Brain · agent and UI contract

Base URL `http://127.0.0.1:8010`. The app loads Filare Labs from the repository's shared `data/`. All data and addresses are synthetic. The `person` argument selects a demo persona. A production service must get identity from an authenticated session.

## Endpoints

| Method | Path | Body / query | Result |
|---|---|---|---|
| GET | `/api/state` | `person` query | `person`, `people`, `mode`, `mode_note`, `voice`, `model`, `company`, `clock`, `sweep_label`, `brief`, `alerts`, `memory`, `candidates`, `decided_candidates`, `proposals`, `outbox`, `sources`, `pending_events`, `runs`, `audit`. Filtered to the demo persona. |
| POST | `/api/sweep` | — | `{runs}` summary list. Simulates the scheduled job across the seven people. |
| POST | `/api/events/{event_id}` | — | `{runs, note?}` summaries. Preset events are `email-006` and `email-008`. |
| POST | `/api/ask` | `{person, question}` | `{run, answer}`. `answer` has `status` (`answered` or `unknown`), `text`, `citations`, and compatibility field `restricted_to: null`. |
| POST | `/api/memory/{id}/approve` or `/reject` | `{person}` | `{memory}`. Promotion uses matching audiences and declines older evidence that would replace an approved record. |
| POST | `/api/proposals/{id}/approve` or `/reject` | `{person}` | `{proposal, outbox_item}`. Approval moves the draft to the mock outbox. |
| GET | `/api/runs/{id}` | `person` query | Full run with ordered steps and token estimates. Ask and brief traces are personal. Ingest traces follow the source ACL. |
| GET | `/api/brief/audio` | `person` query | MP3 of the selected persona’s existing brief. Requires ElevenLabs configuration. |
| POST | `/api/reset` | — | `{ok: true}`. Restores the shared synthetic fixtures. |

Errors include `403` for wrong-person decisions, `404` for unavailable resources, and `409` for decided or stale evidence and overlapping agent operations.

## Key records

- **Citation** includes `id`, `kind`, `label`, `source_id`, `source_title`, `quote`, and `fact` for a memory citation. The UI opens the source only if it is in the current persona's state.
- **Memory** includes `id`, `key`, `topic`, `fact`, `audience`, `source_id`, `quote`, and `status` (`approved`, `candidate`, `rejected`, `superseded`). Conflicts can include `conflicts_with` and `stale_evidence`. Seeded records can include `source_ids`.
- **Brief** includes `person`, `generated_at`, `run_id` and `items`. Items contain `headline`, `why`, `citations` and `proposal_id`.
- **Proposal** has `id`, `owner_role`, optional `owner_id`, draft fields, `citations` and `status` (`pending`, `approved`, `rejected`, `withdrawn`).
- **Run** includes `id`, `agent`, `actor`, `trigger`, `mode`, `model`, `status`, `started_at`, `ms` and `usage`. Full runs also carry `steps` and `output`. `guard` steps mark an application rejection. Gemini usage estimates come from SDK metadata.

The UI's jury walkthrough is in [CHECKS.md](CHECKS.md).
