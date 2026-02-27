"""Tests for SessionEnd hook -- persists patterns to profile."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import date
from typing import Dict, List, Optional

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "session-end.py"
PLUGIN_ROOT = Path(__file__).parent.parent
CONFIRMED_FILE = Path("/tmp/human-speak-confirmed.json")
FLAG_FILE = Path("/tmp/human-speak-flag.json")


def _run_hook(
    confirmed_pairs: Optional[List[Dict[str, object]]] = None,
) -> tuple[subprocess.CompletedProcess[str], Optional[str]]:
    """Run the hook and return (result, profile_content_or_None).

    Profile content is read inside the temp dir context so it survives
    cleanup. FLAG_FILE is NOT pre-deleted so tests can verify hook cleanup.
    """
    if CONFIRMED_FILE.exists():
        CONFIRMED_FILE.unlink()

    if confirmed_pairs is not None:
        CONFIRMED_FILE.write_text(json.dumps(confirmed_pairs))

    with tempfile.TemporaryDirectory() as tmpdir:
        profile_path = Path(tmpdir) / "user-speak-profile.md"

        env = os.environ.copy()
        env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        env["HUMAN_SPEAK_PROFILE_PATH"] = str(profile_path)

        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="{}",
            capture_output=True,
            text=True,
            env=env,
        )
        # Read content while still inside with-block (before temp dir cleanup)
        profile_content = profile_path.read_text() if profile_path.exists() else None
        return result, profile_content


def test_no_confirmed_pairs_exits_cleanly() -> None:
    result, _ = _run_hook(confirmed_pairs=None)
    assert result.returncode == 0


def test_confirmed_pair_written_to_new_profile() -> None:
    pairs = [{"original": "go ahead", "interpreted": "proceed with the plan", "signals": ["missing-subject"]}]
    result, content = _run_hook(pairs)
    assert result.returncode == 0
    assert content is not None, "Profile should have been created"
    assert "go ahead" in content
    assert "proceed with the plan" in content


def test_profile_contains_today_date() -> None:
    pairs = [{"original": "fix it", "interpreted": "fix the auth bug", "signals": ["missing-subject"]}]
    result, content = _run_hook(pairs)
    assert result.returncode == 0
    today = date.today().isoformat()
    assert content is not None
    assert today in content


def test_flag_file_cleaned_up() -> None:
    FLAG_FILE.write_text('{"original": "test", "score": 0.5, "signals": []}')
    _run_hook(confirmed_pairs=None)
    assert not FLAG_FILE.exists(), "Flag file should be deleted after session end"


def test_hook_exits_cleanly_on_bad_confirmed_file() -> None:
    CONFIRMED_FILE.write_text("not valid json {{{")
    result, _ = _run_hook(confirmed_pairs=None)
    assert result.returncode == 0
