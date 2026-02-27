"""Tests for UserPromptSubmit hook behavior."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "user-prompt-submit.py"
FLAG_FILE = Path("/tmp/human-speak-flag.json")


def _run_hook(message: str, threshold: str = "0.4") -> subprocess.CompletedProcess[str]:
    """Run the hook script with the given message as stdin payload."""
    payload = json.dumps({"user_message": message, "session_id": "test"})
    env = os.environ.copy()
    env["HUMAN_SPEAK_THRESHOLD"] = threshold
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )


def setup_function() -> None:
    """Remove flag file before each test."""
    if FLAG_FILE.exists():
        FLAG_FILE.unlink()


def test_clean_message_no_flag_created() -> None:
    result = _run_hook("Fix the bug in auth.py")
    assert result.returncode == 0
    assert not FLAG_FILE.exists(), "Flag file should not be created for clean message"


def test_ambiguous_message_creates_flag() -> None:
    # 22 words + filler words: triggers run-on (>20 words/sentence) + filler-words -> score 0.70
    ambiguous = "you know like i want it to work better and also fix that thing and basically look at the other file too"
    result = _run_hook(ambiguous)
    assert result.returncode == 0
    assert FLAG_FILE.exists(), "Flag file should be created for ambiguous message"


def test_flag_file_contains_expected_fields() -> None:
    _run_hook("you know like i want it to work better and also fix that thing and basically look at the other file too")
    data = json.loads(FLAG_FILE.read_text())
    assert "original" in data
    assert "score" in data
    assert "signals" in data
    assert isinstance(data["score"], float)
    assert isinstance(data["signals"], list)


def test_custom_threshold_respected() -> None:
    # With very low threshold, even a clean message should flag
    result = _run_hook("Fix the bug", threshold="0.0")
    assert result.returncode == 0
    # Score for clean message is 0.0 which equals threshold 0.0 -> should flag
    assert FLAG_FILE.exists()


def test_malformed_json_exits_cleanly() -> None:
    """Hook must not crash on bad input -- exit 0 silently."""
    env = os.environ.copy()
    env["HUMAN_SPEAK_THRESHOLD"] = "0.4"
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input="not valid json {{{{",
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, "Hook must exit 0 on bad input"
    assert not FLAG_FILE.exists()


def test_empty_message_exits_cleanly() -> None:
    result = _run_hook("")
    assert result.returncode == 0
    assert not FLAG_FILE.exists()
