"""Exercise the shared-data jury scenario against a running server."""
import argparse
import json
import sys
from time import monotonic

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("server", nargs="?", default="http://127.0.0.1:8010")
    parser.add_argument("--require-gemini", action="store_true",
                        help="fail if a jury run unexpectedly uses the offline planner")
    args = parser.parse_args()
    started = monotonic()
    runs = []

    loopback = httpx.URL(args.server).host in {"localhost", "127.0.0.1", "::1"}
    with httpx.Client(base_url=args.server, timeout=180, trust_env=not loopback) as client:
        def call(method, path, *, body=None, params=None, status=200):
            response = client.request(method, path, json=body, params=params)
            if response.status_code != status:
                raise RuntimeError(f"{path}: expected HTTP {status}, got {response.status_code} {response.text[:240]}")
            return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text

        def state(person):
            return call("GET", "/api/state", params={"person": person})

        def ask(person, question, expected, source_id=None):
            result = call("POST", "/api/ask", body={"person": person, "question": question})
            answer = result["answer"]
            runs.append(result["run"])
            assert answer["status"] == expected, (person, question, answer)
            if source_id:
                assert source_id in {citation["source_id"] for citation in answer["citations"]}, answer
            else:
                assert not answer["citations"] and answer["text"].startswith("I don't know"), answer
            print(f"  {person} · {result['run']['mode']} · {answer['status']}: {answer['text']}")
            return result

        print(f"Server {args.server} · {state('luca')['mode']}")
        call("POST", "/api/reset")
        assert state("luca")["brief"] is None
        runs.extend(call("POST", "/api/sweep")["runs"])
        luca = state("luca")
        assert luca["company"] == "Filare Labs S.r.l." and luca["brief"]["items"]
        item = luca["brief"]["items"][0]
        assert "14,640" in item["why"] and item["proposal_id"]
        assert not luca["outbox"]
        draft = item["proposal_id"]
        call("POST", f"/api/proposals/{draft}/approve", body={"person": "giulia"}, status=403)
        call("POST", f"/api/proposals/{draft}/approve", body={"person": "luca"})
        assert len(state("luca")["outbox"]) == 1
        print("PASS · scheduled brief and owner-only approval")

        question = "When does the Langhe fix roll out?"
        ask("sara", question, "unknown")
        call("POST", "/api/memory/mem-p01/approve", body={"person": "sara"})
        call("POST", "/api/memory/mem-p02/reject", body={"person": "sara"})
        assert "26 Nov 2026 at 07:00" in ask("sara", question, "answered", "chat-003")["answer"]["text"]
        print("PASS · curated memory and citations")

        ask("giulia", "What is our cash runway?", "answered", "email-003")
        private = ask("sara", "What is our cash runway?", "unknown")
        assert "412,000" not in json.dumps(private) and "mem-002" not in json.dumps(private)
        ask("giulia", "What is our Q2 2027 cloud budget?", "unknown")
        print("PASS · role-specific answers and genuine gaps")

        runs.extend(call("POST", "/api/events/email-006")["runs"])
        conflict, = [alert for alert in state("sara")["alerts"] if alert["source_id"] == "email-006"]
        call("POST", f"/api/memory/{conflict['candidate_id']}/approve", body={"person": "giulia"}, status=409)
        budget = ask("giulia", "What is the Q1 2027 cloud budget?", "answered", "email-005")
        assert "18,000" in budget["answer"]["text"]
        runs.extend(call("POST", "/api/events/email-008")["runs"])
        sara = state("sara")
        assert any(alert["kind"] == "suspicious" and alert["source_id"] == "email-008" for alert in sara["alerts"])
        assert not any(item["source_id"] == "email-008" for item in sara["candidates"])
        assert "Memory review" in call("GET", "/")
        print("PASS · archived claim, suspicious email and workspace")

    modes = ", ".join(sorted({run["mode"] for run in runs}))
    cost = sum(run["usage"]["cost_usd"] for run in runs)
    if args.require_gemini:
        def deliberate_ingest_skip(run):
            return run["agent"] == "ingest" and any(
                step["kind"] == "guard"
                and step["note"].startswith("Checking archived evidence or suspicious content")
                for step in run["steps"]
            )

        unexpected = [run for run in runs
                      if run["agent"] in {"ask", "brief", "ingest"}
                      and run["mode"] != "gemini" and not deliberate_ingest_skip(run)]
        if unexpected:
            print("FAIL · --require-gemini: runs not in gemini mode:")
            for run in unexpected:
                print(f"  {run['id']} · {run['agent']} · {run['trigger']} · {run['mode']}")
            return 1
    print(f"PASS · seven checks · {len(runs)} runs ({modes}) · {monotonic() - started:.1f}s · ${cost:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
