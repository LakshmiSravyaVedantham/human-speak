"""Tests for SessionStart hook -- loads profile and exports threshold."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "session-start.py"
PLUGIN_ROOT = Path(__file__).parent.parent


def _run_hook(profile_content: str | None = None) -> tuple[subprocess.CompletedProcess[str], str]:
    """Run the session-start hook with optional profile content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / "claude.env"
        env_file.write_text("")

        profile_path = PLUGIN_ROOT / "memory" / "user-speak-profile.md"
        original_exists = profile_path.exists()
        original_content = profile_path.read_text() if original_exists else None

        try:
            if profile_content is not None:
                profile_path.write_text(profile_content)
            elif original_exists:
                profile_path.unlink()

            env = os.environ.copy()
            env["CLAUDE_ENV_FILE"] = str(env_file)
            env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)

            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input="{}",
                capture_output=True,
                text=True,
                env=env,
            )
            env_contents = env_file.read_text()
            return result, env_contents
        finally:
            if original_content is not None:
                profile_path.write_text(original_content)
            elif profile_path.exists():
                profile_path.unlink()


def test_loads_threshold_from_profile() -> None:
    profile = "# User Speak Profile\n\n## Calibration\nAmbiguity threshold: 0.35\nLast updated: 2026-02-27\n"
    result, env_contents = _run_hook(profile)
    assert result.returncode == 0
    assert "HUMAN_SPEAK_THRESHOLD=0.35" in env_contents


def test_missing_profile_uses_default() -> None:
    result, env_contents = _run_hook(profile_content=None)
    assert result.returncode == 0
    assert "HUMAN_SPEAK_THRESHOLD=0.40" in env_contents


def test_malformed_profile_uses_default() -> None:
    result, env_contents = _run_hook("this is not valid markdown with threshold")
    assert result.returncode == 0
    assert "HUMAN_SPEAK_THRESHOLD=0.40" in env_contents


def test_hook_exits_cleanly_on_error() -> None:
    """Hook must never crash regardless of environment."""
    env = os.environ.copy()
    env.pop("CLAUDE_ENV_FILE", None)
    env.pop("CLAUDE_PLUGIN_ROOT", None)
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input="{}",
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
