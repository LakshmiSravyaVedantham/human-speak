# human-speak Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Claude Code plugin that detects ambiguous/casual user input, confirms intent before acting, and adapts to a user's communication style over sessions.

**Architecture:** A three-layer plugin: a `UserPromptSubmit` hook scores incoming messages for ambiguity using pure heuristics and writes a flag file; a skill reads the flag and asks Claude to confirm intent before acting; SessionStart/End hooks load and persist a per-user communication profile that calibrates the threshold over time.

**Tech Stack:** Python 3.8+, stdlib only (re, json, os, sys, pathlib), pytest, mypy, Claude Code plugin format (plugin.json, SKILL.md, commands/*.md, hooks/hooks.json)

---

## Task 1: Plugin scaffold

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `hooks/hooks.json`
- Create: `commands/human-speak.md`
- Create: `skills/human-speak/SKILL.md`
- Create: `hooks/scorer.py`
- Create: `hooks/user-prompt-submit.py`
- Create: `hooks/session-start.py`
- Create: `hooks/session-end.py`
- Create: `memory/user-speak-profile.template.md`
- Create: `memory/.gitkeep`
- Create: `tests/__init__.py`
- Create: `README.md`
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `pyproject.toml`

**Step 1: Create directory structure**

```bash
cd /Users/sravyalu/human-speak
mkdir -p .claude-plugin commands skills/human-speak hooks tests memory
touch tests/__init__.py memory/.gitkeep
```

**Step 2: Create plugin manifest**

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "human-speak",
  "version": "0.1.0",
  "description": "Detects ambiguous user input and confirms intent before Claude acts. Adapts to your communication style over time.",
  "author": {
    "name": "Sravya Vedantham",
    "url": "https://github.com/sravyalu"
  },
  "repository": "https://github.com/sravyalu/human-speak",
  "license": "MIT",
  "keywords": ["hooks", "intent", "clarity", "conversation", "ux"],
  "hooks": "./hooks/hooks.json"
}
```

**Step 3: Create hooks registry**

Create `hooks/hooks.json`:

```json
{
  "UserPromptSubmit": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/user-prompt-submit.py",
          "timeout": 5
        }
      ]
    }
  ],
  "SessionStart": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/session-start.py",
          "timeout": 5
        }
      ]
    }
  ],
  "SessionEnd": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/session-end.py",
          "timeout": 5
        }
      ]
    }
  ]
}
```

**Step 4: Create .gitignore**

Create `.gitignore`:

```
__pycache__/
*.pyc
*.pyo
.mypy_cache/
.pytest_cache/
dist/
*.egg-info/
memory/user-speak-profile.md
/tmp/human-speak-flag.json
/tmp/human-speak-confirmed.json
```

**Step 5: Create pyproject.toml for tooling**

Create `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.8"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

**Step 6: Create LICENSE**

Create `LICENSE` with MIT license:

```
MIT License

Copyright (c) 2026 Sravya Vedantham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Step 7: Create README.md**

Create `README.md`:

```markdown
# human-speak

A Claude Code plugin that detects ambiguous or casual user input, confirms intent before Claude acts, and adapts to your communication style over time.

## What it does

- **Hook:** Scores every message for ambiguity (typos, run-ons, missing subjects, filler words)
- **Skill:** When a message is flagged, Claude asks "I think you mean X — is that right?" before acting
- **Memory:** Learns how you communicate and calibrates over sessions

## Install

```bash
claude plugins install https://github.com/sravyalu/human-speak
```

## Usage

Works automatically. For manual invocation: `/human-speak`

## Contributing

PRs welcome. See [docs/plans/](docs/plans/) for architecture.
```

**Step 8: Commit scaffold**

```bash
cd /Users/sravyalu/human-speak
git init
git add .
git commit -m "chore: initialize human-speak plugin scaffold"
```

---

## Task 2: Ambiguity scorer (TDD)

**Files:**
- Create: `hooks/scorer.py`
- Create: `tests/test_scorer.py`

**Step 1: Write failing tests first**

Create `tests/test_scorer.py`:

```python
"""Tests for ambiguity scorer heuristics."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hooks'))

from scorer import score_message, detect_signals


def test_clean_message_scores_low() -> None:
    score = score_message("Fix the bug in auth.py")
    assert score < 0.4, f"Expected < 0.4, got {score}"


def test_run_on_scores_high() -> None:
    msg = ("you know i want it to work better and also fix that thing "
           "and maybe also look at the other file where the problem is")
    score = score_message(msg)
    assert score >= 0.4, f"Expected >= 0.4, got {score}"


def test_filler_words_detected() -> None:
    signals = detect_signals("you know like i want this to work")
    assert "filler-words" in signals


def test_filler_words_case_insensitive() -> None:
    signals = detect_signals("You Know what I mean, Like basically")
    assert "filler-words" in signals


def test_missing_subject_detected() -> None:
    signals = detect_signals("Go ahead with the plan")
    assert "missing-subject" in signals


def test_missing_subject_fix_verb() -> None:
    signals = detect_signals("Fix the broken test")
    assert "missing-subject" in signals


def test_clean_message_no_filler() -> None:
    signals = detect_signals("Please update the README with the new API docs")
    assert "filler-words" not in signals


def test_score_always_in_range() -> None:
    messages = [
        "",
        "ok",
        "Fix auth bug",
        "you know like go ahead and make it work better basically",
        "A" * 500,
    ]
    for msg in messages:
        score = score_message(msg)
        assert 0.0 <= score <= 1.0, f"Score out of range for: {msg[:50]}"


def test_empty_message_no_crash() -> None:
    score = score_message("")
    assert score == 0.0


def test_run_on_signal_long_sentence() -> None:
    # 30-word single sentence = clear run-on
    msg = " ".join(["word"] * 30)
    signals = detect_signals(msg)
    assert "run-on" in signals


def test_short_sentence_no_run_on() -> None:
    signals = detect_signals("Fix the auth bug.")
    assert "run-on" not in signals
```

**Step 2: Run tests — verify they all fail**

```bash
cd /Users/sravyalu/human-speak
pytest tests/test_scorer.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'scorer'` — confirms tests are wired up before implementation.

**Step 3: Implement scorer.py**

Create `hooks/scorer.py`:

```python
"""Ambiguity scorer for user messages.

Scores a message 0.0–1.0 for ambiguity using pure heuristics.
No external dependencies — stdlib only.
"""
from __future__ import annotations

import re

# Filler words that signal casual/verbal input
_FILLERS = frozenset([
    "like", "you know", "sort of", "kinda", "basically",
    "i mean", "right", "literally", "actually",
])

# Common imperative verbs at sentence start (missing subject signals)
_IMPERATIVE_PATTERN = re.compile(
    r"^(go|fix|do|make|add|run|create|update|remove|check|look|try|get|put|set)\b",
    re.IGNORECASE,
)


def detect_signals(text: str) -> list[str]:
    """Return list of ambiguity signal names present in text."""
    if not text.strip():
        return []

    signals: list[str] = []

    # Signal: run-on (many words, few sentences)
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    words = text.split()
    sentence_count = max(len(sentences), 1)
    words_per_sentence = len(words) / sentence_count
    if words_per_sentence > 20:
        signals.append("run-on")

    # Signal: filler-words
    text_lower = text.lower()
    if any(filler in text_lower for filler in _FILLERS):
        signals.append("filler-words")

    # Signal: missing-subject (first sentence starts with imperative verb)
    first_sentence = sentences[0] if sentences else ""
    if _IMPERATIVE_PATTERN.match(first_sentence.strip()):
        signals.append("missing-subject")

    return signals


def score_message(text: str) -> float:
    """Score a message for ambiguity. Returns float 0.0–1.0."""
    if not text.strip():
        return 0.0

    signals = detect_signals(text)

    # Weighted signal contributions
    weights: dict[str, float] = {
        "run-on": 0.35,
        "filler-words": 0.35,
        "missing-subject": 0.30,
    }

    score = sum(weights.get(s, 0.0) for s in signals)
    return min(1.0, max(0.0, score))
```

**Step 4: Run tests — verify they all pass**

```bash
pytest tests/test_scorer.py -v
```

Expected: All 11 tests PASS.

**Step 5: Typecheck**

```bash
mypy hooks/scorer.py
```

Expected: `Success: no issues found in 1 source file`

**Step 6: Commit**

```bash
git add hooks/scorer.py tests/test_scorer.py
git commit -m "feat: add ambiguity scorer with TDD"
```

---

## Task 3: UserPromptSubmit hook (TDD)

**Files:**
- Create: `hooks/user-prompt-submit.py`
- Create: `tests/test_hook.py`

**Step 1: Write failing tests**

Create `tests/test_hook.py`:

```python
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
    ambiguous = "you know like go ahead and fix that thing basically"
    result = _run_hook(ambiguous)
    assert result.returncode == 0
    assert FLAG_FILE.exists(), "Flag file should be created for ambiguous message"


def test_flag_file_contains_expected_fields() -> None:
    _run_hook("you know like go ahead and fix that thing basically")
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
    # Score for clean message is 0.0 which equals threshold 0.0 → should flag
    assert FLAG_FILE.exists()


def test_malformed_json_exits_cleanly() -> None:
    """Hook must not crash on bad input — exit 0 silently."""
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
```

**Step 2: Run tests — verify they fail**

```bash
pytest tests/test_hook.py -v 2>&1 | head -20
```

Expected: Tests fail because `user-prompt-submit.py` doesn't exist yet.

**Step 3: Implement the hook**

Create `hooks/user-prompt-submit.py`:

```python
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
        # Never block the user — fail silently
        pass


if __name__ == "__main__":
    main()
```

**Step 4: Run tests — verify they pass**

```bash
pytest tests/test_hook.py -v
```

Expected: All 6 tests PASS.

**Step 5: Typecheck**

```bash
mypy hooks/user-prompt-submit.py
```

Expected: `Success: no issues found in 1 source file`

**Step 6: Commit**

```bash
git add hooks/user-prompt-submit.py tests/test_hook.py
git commit -m "feat: add UserPromptSubmit hook with TDD"
```

---

## Task 4: human-speak slash command

**Files:**
- Create: `commands/human-speak.md`

**Step 1: Create the command**

Create `commands/human-speak.md`:

```markdown
---
description: Clarify intent of your message before Claude acts on it
argument-hint: [your message or leave blank to clarify last message]
---

You have been invoked as the `/human-speak` command.

## Your job

Help the user clarify what they meant before you take any action.

## Steps

1. Check if `/tmp/human-speak-flag.json` exists and read it.
   - If it exists: you have the original message, score, and signals that triggered this.
   - If it does not exist: the user invoked this manually. Ask them: "What would you like me to do? Describe it in your own words and I'll confirm before acting."

2. Based on the signals detected (or the message content), form your best interpretation of what the user wants.

3. Say exactly: "I think you're asking me to [your interpretation]. Is that right?"
   - Be specific. Do not be vague.
   - One sentence. No preamble.

4. Wait for the user's response.
   - If they say yes (or any affirmative): proceed with the interpreted action.
   - If they correct you: re-interpret using their correction, confirm once more, then act.
   - If they ignore this for one full turn: proceed with your best guess and prepend "Assuming you meant [X]..." to your response.

## What you must NOT do

- Do not act before confirmation
- Do not ask multiple clarifying questions — one interpretation, one confirmation
- Do not change the user's actual request, only clarify it
```

**Step 2: Verify command appears in Claude Code**

```bash
# After installing plugin:
claude plugins install /Users/sravyalu/human-speak
# Then in a Claude Code session, type:
# /human-speak
# Expected: Command appears in autocomplete
```

**Step 3: Commit**

```bash
git add commands/human-speak.md
git commit -m "feat: add /human-speak slash command"
```

---

## Task 5: human-speak auto-trigger skill

**Files:**
- Create: `skills/human-speak/SKILL.md`

**Step 1: Create the skill**

Create `skills/human-speak/SKILL.md`:

```markdown
---
name: human-speak
description: >
  Use this skill when /tmp/human-speak-flag.json exists in the filesystem,
  indicating the UserPromptSubmit hook flagged the user's message as ambiguous.
  Also use when the user's message contains heavy run-on sentences, multiple
  filler words ('you know', 'like', 'basically'), or imperative verbs with no
  clear subject ('go ahead', 'fix that', 'do it').
version: 0.1.0
---

# human-speak Skill

You have been loaded because the user's message was detected as potentially ambiguous.

## Your job

Before acting on the user's message, confirm what they meant.

## Steps

1. Read `/tmp/human-speak-flag.json` if it exists.
   - `original`: the user's raw message
   - `score`: ambiguity score (0.0–1.0)
   - `signals`: list of signals detected (run-on, filler-words, missing-subject)

2. Form ONE clear interpretation of what the user wants.
   Use signals as hints:
   - `run-on` → they have multiple ideas, identify the primary one
   - `filler-words` → casual phrasing, infer the core request
   - `missing-subject` → they told you what to do but not what to do it to — infer from context

3. Ask for confirmation. Format exactly:
   > "I think you're asking me to [specific action]. Is that right?"

4. Wait for response:
   - **Yes / affirmative** → proceed with interpreted action
   - **Correction** → re-interpret, confirm once more, then act
   - **No response after one turn** → proceed, prepend "Assuming you meant [X]..."

## Invariants

- Never act before confirmation
- Never rewrite or repeat back the user's raw message
- One interpretation per confirmation — not a list of options
- Keep your interpretation sentence short (under 15 words)
```

**Step 2: Commit**

```bash
git add skills/human-speak/SKILL.md
git commit -m "feat: add human-speak auto-trigger skill"
```

---

## Task 6: SessionStart hook (TDD)

**Files:**
- Create: `hooks/session-start.py`
- Create: `tests/test_session_start.py`

**Step 1: Write failing tests**

Create `tests/test_session_start.py`:

```python
"""Tests for SessionStart hook — loads profile and exports threshold."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "session-start.py"
PLUGIN_ROOT = Path(__file__).parent.parent


def _run_hook(profile_content: str | None = None) -> subprocess.CompletedProcess[str]:
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
            return result, env_contents  # type: ignore[return-value]
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
```

**Step 2: Run tests — verify they fail**

```bash
pytest tests/test_session_start.py -v 2>&1 | head -15
```

Expected: `FileNotFoundError` — hook doesn't exist yet.

**Step 3: Implement session-start.py**

Create `hooks/session-start.py`:

```python
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
```

**Step 4: Run tests — verify they pass**

```bash
pytest tests/test_session_start.py -v
```

Expected: All 4 tests PASS.

**Step 5: Typecheck**

```bash
mypy hooks/session-start.py
```

**Step 6: Commit**

```bash
git add hooks/session-start.py tests/test_session_start.py
git commit -m "feat: add SessionStart hook with TDD"
```

---

## Task 7: SessionEnd hook (TDD)

**Files:**
- Create: `hooks/session-end.py`
- Create: `memory/user-speak-profile.template.md`
- Create: `tests/test_session_end.py`

**Step 1: Create memory profile template**

Create `memory/user-speak-profile.template.md`:

```markdown
# User Speak Profile

## Communication Patterns
<!-- Examples: "Often omits subjects", "Uses voice-style run-ons" -->

## Calibration
Ambiguity threshold: 0.40
Last updated: YYYY-MM-DD

## Confirmed Intent Mappings
<!-- Format: - "raw phrase" → interpreted as: "specific action" -->
```

**Step 2: Write failing tests**

Create `tests/test_session_end.py`:

```python
"""Tests for SessionEnd hook — persists patterns to profile."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import date

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "session-end.py"
PLUGIN_ROOT = Path(__file__).parent.parent
CONFIRMED_FILE = Path("/tmp/human-speak-confirmed.json")
FLAG_FILE = Path("/tmp/human-speak-flag.json")


def _run_hook(confirmed_pairs: list | None = None) -> tuple[subprocess.CompletedProcess[str], Path]:
    if CONFIRMED_FILE.exists():
        CONFIRMED_FILE.unlink()
    if FLAG_FILE.exists():
        FLAG_FILE.unlink()

    if confirmed_pairs:
        CONFIRMED_FILE.write_text(json.dumps(confirmed_pairs))

    with tempfile.TemporaryDirectory() as tmpdir:
        profile_path = Path(tmpdir) / "user-speak-profile.md"
        template = PLUGIN_ROOT / "memory" / "user-speak-profile.template.md"

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
        return result, profile_path


def test_no_confirmed_pairs_exits_cleanly() -> None:
    result, _ = _run_hook(confirmed_pairs=None)
    assert result.returncode == 0


def test_confirmed_pair_written_to_new_profile() -> None:
    pairs = [{"original": "go ahead", "interpreted": "proceed with the plan", "signals": ["missing-subject"]}]
    result, profile_path = _run_hook(pairs)
    assert result.returncode == 0
    assert profile_path.exists()
    content = profile_path.read_text()
    assert "go ahead" in content
    assert "proceed with the plan" in content


def test_profile_contains_today_date() -> None:
    pairs = [{"original": "fix it", "interpreted": "fix the auth bug", "signals": ["missing-subject"]}]
    result, profile_path = _run_hook(pairs)
    assert result.returncode == 0
    today = date.today().isoformat()
    content = profile_path.read_text()
    assert today in content


def test_flag_file_cleaned_up() -> None:
    FLAG_FILE.write_text('{"original": "test", "score": 0.5, "signals": []}')
    _run_hook(confirmed_pairs=None)
    assert not FLAG_FILE.exists(), "Flag file should be deleted after session end"


def test_hook_exits_cleanly_on_bad_confirmed_file() -> None:
    CONFIRMED_FILE.write_text("not valid json {{{")
    result, _ = _run_hook(confirmed_pairs=None)
    assert result.returncode == 0
```

**Step 3: Run tests — verify they fail**

```bash
pytest tests/test_session_end.py -v 2>&1 | head -15
```

**Step 4: Implement session-end.py**

Create `hooks/session-end.py`:

```python
"""SessionEnd hook: persists confirmed intent patterns to user profile."""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

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


def _initialize_profile(profile_path: Path) -> str:
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
        pairs: list[dict[str, object]] = []
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
                content = _initialize_profile(profile_path)

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
                    new_lines.append(f'- "{original}" → interpreted as: "{interpreted}"')

            if new_lines:
                if "## Confirmed Intent Mappings" in content:
                    content = content + "\n" + "\n".join(new_lines)
                else:
                    content = content + "\n## Confirmed Intent Mappings\n" + "\n".join(new_lines)

            # Enforce max mappings: keep last MAX_MAPPINGS entries
            mapping_lines = [l for l in content.splitlines() if l.startswith('- "')]
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
```

**Step 5: Run tests — verify they pass**

```bash
pytest tests/test_session_end.py -v
```

Expected: All 5 tests PASS.

**Step 6: Typecheck**

```bash
mypy hooks/session-end.py
```

**Step 7: Commit**

```bash
git add hooks/session-end.py memory/user-speak-profile.template.md memory/.gitkeep tests/test_session_end.py
git commit -m "feat: add SessionEnd hook and memory profile template with TDD"
```

---

## Task 8: Full test suite + GitHub setup

**Files:**
- Verify: All tests pass together
- Create: `.github/workflows/ci.yml`
- Create: GitHub repo and push

**Step 1: Run full test suite**

```bash
cd /Users/sravyalu/human-speak
pytest tests/ -v --tb=short
```

Expected: All tests PASS. Note the total count.

**Step 2: Typecheck all hooks**

```bash
mypy hooks/scorer.py hooks/user-prompt-submit.py hooks/session-start.py hooks/session-end.py
```

Expected: `Success: no issues found in 4 source files`

**Step 3: Create GitHub Actions CI**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.10", "3.12"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install test dependencies
        run: pip install pytest mypy
      - name: Typecheck
        run: mypy hooks/scorer.py hooks/user-prompt-submit.py hooks/session-start.py hooks/session-end.py
      - name: Run tests
        run: pytest tests/ -v
```

**Step 4: Create GitHub repo and push**

```bash
cd /Users/sravyalu/human-speak
git add .github/
git commit -m "chore: add GitHub Actions CI"

# Create repo on GitHub (requires gh CLI)
gh repo create sravyalu/human-speak --public --description "Claude Code plugin: detects ambiguous input, confirms intent, adapts to your communication style" --source . --push
```

**Step 5: Verify CI passes on GitHub**

```bash
gh run list --repo sravyalu/human-speak --limit 1
```

Expected: Status = `completed`, conclusion = `success`

**Step 6: Add GitHub topics**

```bash
gh repo edit sravyalu/human-speak --add-topic "claude-code" --add-topic "claude-plugin" --add-topic "hooks" --add-topic "nlp" --add-topic "intent-detection"
```

---

## Task 9: Manual acceptance test (fresh-clone simulation)

**Goal:** Verify the plugin works end-to-end as a real user would install it.

**Step 1: Clone fresh**

```bash
git clone https://github.com/sravyalu/human-speak /tmp/human-speak-test
```

**Step 2: Install plugin**

```bash
claude plugins install /tmp/human-speak-test
```

**Step 3: Verify hook triggers**

In a new Claude Code session:
1. Type: `Fix the bug in auth.py` — hook should NOT trigger (clean message)
2. Type: `you know like go ahead and fix that thing basically` — hook SHOULD trigger, skill should ask for confirmation
3. Reply: `yes, fix the authentication bug in auth.py` — Claude should proceed
4. End session — check that profile was created at plugin's `memory/user-speak-profile.md`

**Step 4: Verify profile persists**

```bash
cat ~/.claude/plugins/installed/human-speak/memory/user-speak-profile.md
```

Expected: File exists with today's date and at least one confirmed mapping.

**Step 5: Start new session — verify threshold loads**

In a new Claude Code session, verify the SessionStart hook loaded the profile (check stderr output or threshold value).

---

## Done

The plugin is complete when:
- [ ] All pytest tests pass
- [ ] mypy reports no errors on all 4 hook files
- [ ] GitHub Actions CI passes on 3 Python versions
- [ ] Manual acceptance test completes successfully
- [ ] GitHub repo is public with README, LICENSE, CI badge, and topics
