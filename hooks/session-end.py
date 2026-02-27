"""SessionEnd hook: persists confirmed intent patterns to user profile."""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

CONFIRMED_FILE = Path("/tmp/human-speak-confirmed.json")
FLAG_FILE = Path("/tmp/human-speak-flag.json")
MAX_MAPPINGS = 20


def _get_profile_path() -> Path:
    override = os.environ.get("HUMAN_SPEAK_PROFILE_PATH")
    if override:
        return Path(override)
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).parent.parent))
    return Path(plugin_root) / "memory" / "user-speak-profile.md"


def _get_template_path() -> Path:
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).parent.parent))
    return Path(plugin_root) / "memory" / "user-speak-profile.template.md"


def _initialize_profile() -> str:
    template = _get_template_path()
    if template.exists():
        return template.read_text()
    return (
        "# User Speak Profile\n\n"
        "## Calibration\n"
        "Ambiguity threshold: 0.40\n"
        f"Last updated: {date.today().isoformat()}\n\n"
        "## Confirmed Intent Mappings\n"
    )


def main() -> None:
    try:
        # Read confirmed pairs (may not exist)
        pairs: List[Dict[str, object]] = []
        if CONFIRMED_FILE.exists():
            try:
                pairs = json.loads(CONFIRMED_FILE.read_text())
            except (json.JSONDecodeError, ValueError):
                pairs = []

        if pairs:
            profile_path = _get_profile_path()

            if profile_path.exists():
                content = profile_path.read_text()
            else:
                content = _initialize_profile()

            # Update date
            today = date.today().isoformat()
            if "Last updated:" in content:
                lines = content.splitlines()
                content = "\n".join(
                    f"Last updated: {today}" if line.startswith("Last updated:") else line
                    for line in lines
                )

            # Append new mappings under Confirmed Intent Mappings section
            new_lines = []
            for pair in pairs:
                original = pair.get("original", "")
                interpreted = pair.get("interpreted", "")
                if original and interpreted:
                    new_lines.append(f'- "{original}" -> interpreted as: "{interpreted}"')

            if new_lines:
                if "## Confirmed Intent Mappings" in content:
                    content = content + "\n" + "\n".join(new_lines)
                else:
                    content = content + "\n## Confirmed Intent Mappings\n" + "\n".join(new_lines)

            # Enforce max mappings: keep last MAX_MAPPINGS entries
            mapping_lines = [ln for ln in content.splitlines() if ln.startswith('- "')]
            if len(mapping_lines) > MAX_MAPPINGS:
                excess = len(mapping_lines) - MAX_MAPPINGS
                for old_line in mapping_lines[:excess]:
                    content = content.replace(old_line + "\n", "")

            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(content)

        # Clean up temp files
        for f in [CONFIRMED_FILE, FLAG_FILE]:
            if f.exists():
                f.unlink()

    except Exception:
        # Never crash on session end
        pass


if __name__ == "__main__":
    main()
