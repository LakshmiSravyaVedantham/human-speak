# Design: human-speak Claude Code Plugin

**Date:** 2026-02-27
**Author:** Sravya Vedantham
**Status:** Approved

---

## Overview

A Claude Code plugin that makes Claude better at understanding casual, voice-style, and typo-heavy human input. Most users who type fast or think out loud produce messy messages — run-ons, missing subjects, filler words, typos. Claude sometimes misinterprets these. This plugin detects ambiguous input automatically and asks for confirmation before acting, without ever silently rewriting the user's words.

---

## Architecture

```
User types messy message
        ↓
[Hook: UserPromptSubmit]
  → Scores the message for ambiguity (pure heuristics, no API call)
  → If score < threshold: pass through unchanged
  → If score ≥ threshold: write flag to /tmp/human-speak-flag.json
        ↓
[Skill: /human-speak]
  → Triggered automatically when hook flag is present
  → Claude interprets likely intent and asks: "Did you mean X?"
  → User confirms or corrects before Claude acts
        ↓
[Memory: memory/user-speak-profile.md]
  → SessionStart hook loads profile, sets threshold
  → SessionEnd hook appends confirmed interpretation patterns
  → Over time: fewer false positives, better calibration per user
```

**Contribution path:** Public GitHub repo `sravyalu/human-speak`, structured as a valid Claude Code plugin, publishable to the official marketplace.

---

## Components

### Component 1: Ambiguity Scorer — `hooks/scorer.py`

A pure Python module (no external dependencies beyond stdlib) with the following functions:

- `score_message(text: str) -> float` — returns 0.0–1.0 ambiguity score
- `detect_signals(text: str) -> list[str]` — returns list of signal names detected

**Signals detected:**
- `run-on` — word count vs sentence count ratio above threshold
- `typo-density` — high proportion of non-dictionary words
- `missing-subject` — sentence starts with verb or imperative without subject
- `filler-words` — presence of "like", "you know", "sort of", "kinda", "basically"

### Component 2: UserPromptSubmit Hook — `hooks/user-prompt-submit.py`

Fires on every user message. Uses scorer.py. Writes a flag JSON file if ambiguity score meets threshold.

- Reads threshold from profile (default: 0.4)
- Flag file: `/tmp/human-speak-flag.json` with `{original, score, signals}`
- **Never rewrites the user's message**
- **Never blocks the message**
- Fails silently on any error

### Component 3: human-speak Skill — `skills/human-speak/SKILL.md`

Loaded automatically when flag file is present. Also invocable manually via `/human-speak`.

- Reads flag file to understand what signals were detected
- Claude surfaces interpretation: "I think you're asking me to X. Is that right?"
- Waits for explicit user confirmation before acting
- If user corrects: re-interprets and confirms again
- If invoked manually with no flag: asks generically "What did you mean?"

### Component 4: SessionStart Hook — `hooks/session-start.py`

Runs at session start. Loads `memory/user-speak-profile.md` if it exists. Exports threshold to session context. Falls back to defaults if profile is missing or malformed.

### Component 5: SessionEnd Hook — `hooks/session-end.py`

Runs at session end. Reads confirmed interpretation pairs from the session. Appends new patterns to `memory/user-speak-profile.md`. Recalibrates threshold based on false positive rate.

### Component 6: Memory Profile — `memory/user-speak-profile.md`

Markdown file persisting across sessions. Stores communication patterns, calibrated threshold, and confirmed intent mappings. Never stores message content — only structural patterns.

---

## Data Flow

```
SESSION START
  └── SessionStart hook loads user-speak-profile.md
  └── Sets threshold (default 0.4 if no profile)

USER TYPES MESSAGE
  └── UserPromptSubmit hook fires
        ├── Score < threshold → exit silently
        └── Score ≥ threshold → write /tmp/human-speak-flag.json

CLAUDE RECEIVES MESSAGE
  └── System context contains flag → loads human-speak skill
  └── Claude surfaces interpretation + confirmation request
  └── User confirms or corrects

CLAUDE ACTS
  └── Proceeds with confirmed intent

SESSION END
  └── SessionEnd hook appends confirmed pairs to profile
  └── Recalibrates threshold
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Hook script crashes | Fail silently — message passes through unblocked |
| Flag file missing when skill loads | Ask generically "What did you mean?" |
| Profile missing or malformed | Use defaults, log warning, no crash |
| User ignores clarification | Claude waits one turn, then proceeds with best-guess |
| Too many false positives | `/human-speak calibrate` raises threshold manually |
| Borderline score (±0.02 of threshold) | Log but do not flag |

**Key invariants:**
- Hook never modifies the user's message
- Skill never acts without user confirmation
- Memory never stores message content
- Everything degrades gracefully

---

## Testing Strategy

### Unit Tests (`tests/test_scorer.py`)
- Clean message scores below threshold
- Run-on message scores above threshold
- Missing subject detected correctly
- Typo density calculated correctly
- Threshold is configurable from profile
- Hook fails silently on error

### Integration Tests (`tests/test_skill.py`)
- Flag present → skill asks for confirmation
- User confirms → Claude acts on interpreted intent
- User corrects → Claude re-interprets
- Manual invocation with no flag → generic clarification

### Memory Tests (`tests/test_memory.py`)
- Profile threshold loads correctly
- Session end appends new pattern
- Malformed profile falls back to defaults

### Manual Acceptance Test
1. Fresh clone to `/tmp/`
2. `claude plugins install /tmp/human-speak-test`
3. Send clean message → hook should not trigger
4. Send messy message → hook flags, skill asks for confirmation
5. Confirm intent → Claude proceeds
6. End session → profile updated
7. New session → threshold loads from profile

---

## Success Criteria

- Zero interference for clean messages (hook exits in < 10ms)
- Ambiguous messages flagged within single message round-trip
- User can confirm or correct intent in one reply
- Profile grows across sessions without manual maintenance
- Plugin installable in one command from GitHub

---

## Open Questions

- Should `/human-speak calibrate` be a separate command or sub-argument to the skill?
- Should the profile be per-project or global (per-user)?
- Threshold for MVP: 0.4 — validate with real usage before adjusting
