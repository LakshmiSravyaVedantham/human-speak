"""SessionStart hook: loads user speak profile and exports threshold."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

DEFAULT_THRESHOLD = 0.40
THRESHOLD_PATTERN = re.compile(r"Ambiguity threshold:\s*([\d.]+)")


def _find_profile() -> Path:
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).parent.parent))
    return Path(plugin_root) / "memory" / "user-speak-profile.md"


def _parse_threshold(content: str) -> float:
    match = THRESHOLD_PATTERN.search(content)
    if match:
        return float(match.group(1))
    raise ValueError("Threshold not found in profile")


def _export_threshold(value: float) -> None:
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    line = f"HUMAN_SPEAK_THRESHOLD={value:.2f}\n"
    if env_file:
        with open(env_file, "a") as f:
            f.write(line)
    else:
        os.environ["HUMAN_SPEAK_THRESHOLD"] = f"{value:.2f}"


def main() -> None:
    try:
        profile = _find_profile()
        if profile.exists():
            content = profile.read_text()
            try:
                threshold = _parse_threshold(content)
            except (ValueError, AttributeError):
                print("human-speak: malformed profile, using default threshold", file=sys.stderr)
                threshold = DEFAULT_THRESHOLD
        else:
            threshold = DEFAULT_THRESHOLD
        _export_threshold(threshold)
    except Exception:
        # Never crash the session
        pass


if __name__ == "__main__":
    main()
