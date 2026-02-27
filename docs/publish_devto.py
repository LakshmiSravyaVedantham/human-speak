"""Publish the human-speak blog post to Dev.to."""
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

key = os.environ.get("DEVTO_API_KEY")
if not key:
    raise SystemExit("Error: DEVTO_API_KEY not set. Run: export DEVTO_API_KEY=<your-key>")

body = (Path(__file__).parent / "blog-post-devto.md").read_text()

payload = json.dumps({
    "article": {
        "title": 'I built a Claude Code plugin that asks "did you mean...?" before acting on vague prompts',
        "published": True,
        "tags": ["claudecode", "ai", "python", "opensource"],
        "body_markdown": body,
    }
}).encode()

req = urllib.request.Request(
    "https://dev.to/api/articles",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Accept": "application/vnd.forem.api-v1+json",
        "api-key": key,
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        print("Published successfully!")
        print("URL:", data["url"])
        print("ID: ", data["id"])
except urllib.error.HTTPError as e:
    print(f"Error {e.code}:", e.read().decode())
