"""UserPromptSubmit hook: scores user messages for ambiguity.

Reads JSON payload from stdin. Writes a flag file if score >= threshold.
Never modifies the user's message. Exits 0 on any error.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add hooks directory to path for scorer import
sys.path.insert(0, str(Path(__file__).parent))

FLAG_FILE = Path("/tmp/human-speak-flag.json")
DEFAULT_THRESHOLD = 0.4


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)

        message: str = payload.get("user_message", "")
        if not message.strip():
            return

        threshold = float(os.environ.get("HUMAN_SPEAK_THRESHOLD", DEFAULT_THRESHOLD))

        from scorer import detect_signals, score_message
        score = score_message(message)
        signals = detect_signals(message)

        if score >= threshold:
            FLAG_FILE.write_text(json.dumps({
                "original": message,
                "score": round(score, 4),
                "signals": signals,
            }))
    except Exception:
        # Never block the user -- fail silently
        pass


if __name__ == "__main__":
    main()
