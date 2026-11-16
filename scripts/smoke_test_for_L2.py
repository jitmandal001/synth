"""Check every Synth endpoint against a running server.

Start the app first, then run this in a second terminal:

    python scripts/smoke_test.py          # no LLM calls, nothing saved
    python scripts/smoke_test.py --llm    # also runs two real extractions
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--llm", action="store_true", help="also run real LLM extractions")
parser.add_argument("--base-url", default="http://127.0.0.1:8000")
args = parser.parse_args()


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        args.base_url + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"null")


results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name:<36} {detail}")


try:
    call("GET", "/health")
except urllib.error.URLError:
    sys.exit(f"Synth is not running at {args.base_url}. Start it first.")

# Basic endpoints
status, body = call("GET", "/")
check("GET /", status == 200, str(status))

status, body = call("GET", "/health")
check("GET /health", status == 200, f"{status} {body}")

# /extract input validation (no LLM call happens for these)
status, _ = call("POST", "/extract", {})
check("POST /extract with neither field", status == 400, str(status))

status, _ = call("POST", "/extract", {"abstract": "x", "arxiv_id": "1706.03762"})
check("POST /extract with both fields", status == 400, str(status))

status, _ = call("POST", "/extract", {"abstract": ""})
check("POST /extract with empty abstract", status == 422, str(status))

status, _ = call("POST", "/extract", {"arxiv_id": "not-an-id"})
check("POST /extract malformed arXiv ID", status == 400, str(status))

status, _ = call("POST", "/extract", {"arxiv_id": "9999.99999"})
check("POST /extract unknown arXiv ID", status == 404, str(status))

# Reading stored documents
status, documents = call("GET", "/documents")
is_list = status == 200 and isinstance(documents, list)
check("GET /documents", is_list, f"{status}, {len(documents) if is_list else '?'} documents")

if is_list and documents:
    first_id = documents[0]["id"]
    status, body = call("GET", f"/documents/{first_id}")
    check("GET /documents/{id}", status == 200 and body["id"] == first_id, str(status))

status, body = call("GET", "/documents?category=no-such-category")
check("GET /documents?category=...", status == 200 and body == [], str(status))

status, _ = call("GET", "/documents/999999999")
check("GET /documents/{unknown id}", status == 404, str(status))

# Real extractions: these call the LLM and save to the database
if args.llm:
    abstract = (
        f"Smoke test {int(time.time())}: we propose a transformer-based "
        "model for classifying scientific documents."
    )
    status, body = call("POST", "/extract", {"abstract": abstract})
    check("POST /extract abstract (LLM)", status == 200 and "summary" in body, str(status))

    status, documents = call("GET", "/documents")
    saved = [d for d in documents if d["abstract"] == abstract] if status == 200 else []
    check(
        "extraction saved to the database",
        len(saved) == 1 and len(saved[0]["extractions"]) == 1,
        f"{len(saved)} matching document(s)",
    )

    status, body = call("POST", "/extract", {"arxiv_id": "1706.03762"})
    check("POST /extract arxiv_id (LLM)", status == 200 and "summary" in body, str(status))

passed = sum(results)
print(f"\n{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
