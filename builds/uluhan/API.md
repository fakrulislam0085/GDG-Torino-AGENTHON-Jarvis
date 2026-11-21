# Company Brain — agent ↔ UI contract

Owner: agent lead (Uluhan). The UI builds against this. If a field changes, this file changes in the same commit.

Base URL: `http://127.0.0.1:8000` (local). All bodies are JSON. **Demo data only — the company, people and messages are fictional.**

The acting person is always sent by the UI (`person`), never chosen by the model. Every permission check happens in the tool layer, before Gemini sees any data.

## People (fixed in demo data)

| id | name | role |
|---|---|---|
| `giulia` | Giulia Rinaldi | `finance` |
| `marco` | Marco Bellini | `tech` |

## Endpoints

| Method | Path | Body | Returns | Jury check |
|---|---|---|---|---|
| GET | `/api/state?person=giulia` | — | `State` (filtered to what this person may see) | all |
| POST | `/api/sweep` | `{}` | `{runs: Run[]}` — the 08:00 background sweep: ingests overnight sources, writes each person's brief | 1 speaks first |
| POST | `/api/events/{event_id}` | `{}` | `{runs: Run[]}` — a new email arrives live (`nordprint_terms`, `injection`) | 1, red team |
| POST | `/api/ask` | `{person, question}` | `{run: Run, answer: Answer}` | 3, 4, 5 |
| POST | `/api/memory/{id}/approve` | `{person}` | `{memory: Memory}` | 2 |
| POST | `/api/memory/{id}/reject` | `{person}` | `{memory: Memory}` | 2 |
| POST | `/api/proposals/{id}/approve` | `{person}` | `{proposal: Proposal, outbox_item}` | 6 |
| POST | `/api/proposals/{id}/reject` | `{person}` | `{proposal: Proposal}` | 6 |
| POST | `/api/reset` | `{}` | `{ok: true}` | — |
| GET | `/api/runs/{run_id}?person=giulia` | — | `Run` (full trace; only runs this person may see) | trace |

Errors: `403 {detail}` when the person is not allowed (e.g. tech approving a finance memory), `404` unknown id, `409` already decided.

## Types

```jsonc
// State
{
  "person": {"id": "giulia", "name": "Giulia Rinaldi", "role": "finance"},
  "mode": "gemini" | "offline",        // show as a badge; offline = deterministic fallback, no model
  "model": "gemini-3.8-flash",
  "clock": "2026-12-07T08:00",
  "brief": Brief | null,               // null until the sweep has run
  "alerts": Alert[],                   // things the brain raised on its own (conflicts, suspicious input)
  "memory": Memory[],                  // approved + superseded items this person may see
  "candidates": Memory[],              // status "candidate", awaiting a human
  "proposals": Proposal[],
  "outbox": OutboxItem[],              // mock outbox: nothing is really sent
  "sources": Source[],
  "pending_events": [{"id": "nordprint_terms", "label": "..."}],
  "runs": RunSummary[],                // newest first
  "audit": AuditEntry[]
}

// Memory
{
  "id": "M3", "key": "atlas.fee", "topic": "Atlas fee and milestones",
  "fact": "Atlas fixed fee is €84,000 ...",
  "audience": ["finance"],             // or ["all"]
  "status": "approved" | "candidate" | "rejected" | "superseded",
  "source_id": "D2", "quote": "exact text from the source",
  "conflicts_with": "M4" | null,       // candidate that contradicts an approved item
  "superseded_by": "M9" | null,
  "decided_by": "giulia" | null, "decided_at": "..." | null
}

// Answer  (what /api/ask shows in the chat)
{
  "status": "answered" | "restricted" | "unknown",
  "text": "Send it to ap@verdi-logistics.example.",   // for restricted/unknown the text is fixed by code, not the model
  "citations": [{"id": "M8", "kind": "memory", "label": "Verdi invoice address", "source_id": "CH2", "source_title": "..."}],
  "restricted_to": ["finance"] | null
}

// Brief
{
  "person": "giulia", "generated_at": "2026-12-07T08:00", "run_id": "r_...",
  "items": [{
    "headline": "Verdi signed off staging — milestone 2 (€28,000) is now invoiceable",
    "why": "...",
    "citations": [Citation],
    "proposal_id": "P1" | null
  }]
}

// Alert
{"id": "A1", "kind": "conflict" | "suspicious", "to_roles": ["finance"], "text": "...",
 "memory_id": "M4", "candidate_id": "M10", "source_id": "L1", "created_at": "..."}

// Proposal  (check 6: nothing happens until a person approves)
{
  "id": "P1", "kind": "email", "owner_role": "finance",
  "to": "ap@verdi-logistics.example", "subject": "...", "body": "...",
  "reason": "...", "citations": [Citation],
  "status": "pending" | "approved" | "rejected",
  "decided_by": null, "decided_at": null, "run_id": "r_..."
}

// Run  (the agent trace — render as a live timeline)
{
  "id": "r_ab12", "agent": "ask" | "brief" | "ingest",
  "actor": "giulia" | "system", "trigger": "question" | "08:00 sweep" | "new email L1",
  "mode": "gemini" | "offline", "model": "gemini-3.8-flash",
  "status": "done" | "error",
  "started_at": "...", "ms": 2140,
  "steps": [{
    "i": 1,
    "kind": "trigger" | "tool_call" | "tool_result" | "guard" | "model_text" | "fallback",
    "tool": "search_memory" | null,
    "args": {...} | null,
    "result": {...} | null,           // already permission-filtered
    "note": "human-readable line for the timeline",
    "ms": 312
  }],
  "usage": {"input_tokens": 1830, "output_tokens": 210, "cost_usd": 0.0021}
}
```

`guard` steps are code refusing something the model tried (e.g. a citation it may not use, a recipient not on record, a quote not in the source). Show them: they are the trust story.

## Demo script these endpoints support

1. `POST /api/reset`, then `POST /api/sweep` → each person's DM shows a brief at 08:00. **(1, 7)**
2. Giulia asks *"Where should we send the Atlas milestone 2 invoice?"* → `unknown`. She approves candidate `M8` (invoice address) and rejects `M9` (launch-slip rumour). Ask again → answered, cites `M8`. **(2, 4, 5)**
3. Ask *"How much is Atlas milestone 2?"* as Giulia → €28,000 with citation; as Marco → `restricted`. **(3)**
4. Ask *"What is the budget for the Atlas mobile app?"* → `unknown`. **(5)**
5. Proposal `P1` (milestone-2 invoice email) is `pending`; outbox empty; approve → outbox has it. **(6)**
6. `POST /api/events/nordprint_terms` → conflict alert to finance, plus a pending reply asking for a signed amendment.
7. `POST /api/events/injection` → flagged suspicious, nothing approved, nothing sent.
