"""One tiny Gemini call through Vertex AI, to prove credentials, project, region and model id work.

Run from builds/uluhan:  ../../.venv/bin/python check_gemini.py
Costs a fraction of a cent. Prints the model's reply, token counts and the cost estimate.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brain import env  # noqa: E402

env.load()
from brain import agents  # noqa: E402

print("project :", os.getenv("GOOGLE_CLOUD_PROJECT") or "(not set)")
print("location:", os.getenv("GOOGLE_CLOUD_LOCATION", "eu"))
print("model   :", agents.MODEL)
c = agents.client()
if c is None:
    print("\nNo client:", agents.mode_note() or "check .env")
    sys.exit(1)
t = time.time()
try:
    r = c.models.generate_content(model=agents.MODEL, contents="Reply with exactly: OK from Vertex")
except Exception as e:
    print(f"\nFAILED: {type(e).__name__}: {str(e)[:500]}")
    print("Hints: 'PERMISSION_DENIED' -> your account needs the Vertex AI User role on the project;"
          " 'NOT_FOUND' -> model id or region; 'DefaultCredentialsError' -> run gcloud auth application-default login")
    sys.exit(2)
u = r.usage_metadata
out = (u.candidates_token_count or 0) + (getattr(u, "thoughts_token_count", 0) or 0)
print(f"\nreply   : {r.text!r}")
print(f"tokens  : {u.prompt_token_count} in / {out} out  ->  ${u.prompt_token_count * agents.PRICE_IN + out * agents.PRICE_OUT:.6f}")
print(f"latency : {time.time() - t:.2f}s")
