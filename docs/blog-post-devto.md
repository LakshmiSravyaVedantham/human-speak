# I built a Claude Code plugin that asks "did you mean...?" before acting on vague prompts

Ever typed something like *"you know, go ahead and fix that thing"* into Claude and watched it confidently do the wrong thing?

I did it enough times to build a fix: **human-speak** — a Claude Code plugin that scores every message for ambiguity, confirms intent before acting, and learns your communication style over sessions.

## The problem

I tend to think out loud when I code. My prompts drift into run-ons, filler words, and missing subjects. Claude is too obliging — it always picks an interpretation and runs with it. Half the time it's the wrong one, and I've already lost context by the time I notice.

What I wanted: *one confirmation step before Claude acts on anything vague.*

## What it does

```bash
# Install
claude plugins install https://github.com/LakshmiSravyaVedantham/human-speak

# Works automatically — no command needed
# Or trigger manually:
/human-speak
```

When you send a message like:

> *"you know like i want it to work better and also fix that thing basically"*

Claude responds:

> *"I think you're asking me to fix the authentication bug in auth.py. Is that right?"*

You say yes. It acts. No wasted turns.

## Architecture: three layers

The plugin uses Claude Code's hook system — small Python scripts that fire at specific lifecycle events.

### Layer 1: UserPromptSubmit hook

Every message gets scored 0.0–1.0 for ambiguity using three pure-heuristic signals:

| Signal | What it catches | Weight |
|---|---|---|
| `run-on` | >20 words per sentence | 0.35 |
| `filler-words` | "like", "you know", "basically"… | 0.35 |
| `missing-subject` | Imperative verb at sentence start | 0.30 |

If score ≥ threshold (default 0.4), it writes a flag file at `/tmp/human-speak-flag.json`.

```python
# The scorer — pure stdlib, zero dependencies
def score_message(text: str) -> float:
    if not text.strip():
        return 0.0
    signals = detect_signals(text)
    weights = {"run-on": 0.35, "filler-words": 0.35, "missing-subject": 0.30}
    return min(1.0, sum(weights.get(s, 0.0) for s in signals))
```

### Layer 2: Skill

When the flag file exists, Claude loads the skill before responding. The skill has one job: form one interpretation, ask one confirmation question, wait.

```
Ask for confirmation. Format exactly:
"I think you're asking me to [specific action]. Is that right?"

Invariants:
- Never act before confirmation
- One interpretation per confirmation — not a list of options
- Keep your interpretation under 15 words
```

### Layer 3: SessionStart/End hooks

`session-start.py` reads your profile and exports your calibrated threshold as an env var before the session begins.

`session-end.py` persists confirmed intent pairs to `memory/user-speak-profile.md`:

```markdown
## Confirmed Intent Mappings
- "go ahead" → interpreted as: "proceed with the current plan"
- "fix that thing" → interpreted as: "fix the auth bug in auth.py"
```

Over time, the plugin learns what your vague phrases actually mean.

## How I built it: full TDD with zero dependencies

Constraints I set for myself:

- **No external packages** — stdlib only (`re`, `json`, `os`, `pathlib`)
- **Tests before implementation** — every file got failing tests first
- **mypy strict** — type-annotated throughout

This made the hook scripts surprisingly easy to test. Each hook reads from stdin and writes to files — totally mockable with `subprocess.run(..., input=payload)`.

One thing that bit me: `str | None` union syntax is Python 3.10+. My CI matrix included 3.9, which caught it immediately. The fix was a one-liner (`Optional[str]`), but it's the kind of thing that would have silently broken a user on an older Python.

## CI

GitHub Actions matrix across Python 3.9, 3.10, 3.12. 26 tests, all passing.

```yaml
strategy:
  matrix:
    python-version: ["3.9", "3.10", "3.12"]
steps:
  - run: pip install pytest mypy
  - run: mypy hooks/scorer.py hooks/user-prompt-submit.py hooks/session-start.py hooks/session-end.py
  - run: pytest tests/ -v
```

## What I learned

**Hooks are underrated.** The Claude Code hook system is small but composable. A 40-line Python script that fires before every prompt can meaningfully change how the model behaves — without touching the model itself.

**TDD pays off on filesystem-heavy code.** Hooks read from stdin, write temp files, and load env vars. Those boundaries are easy to mock and the test harness caught three real bugs during development.

**One confirmation is better than zero or many.** The skill's invariant — *one interpretation, one question* — was the hardest part to get right in the SKILL.md. It's easy to write a clarification flow that asks too many questions and becomes more annoying than just letting Claude guess.

## Try it

```bash
claude plugins install https://github.com/LakshmiSravyaVedantham/human-speak
```

Repo: [github.com/LakshmiSravyaVedantham/human-speak](https://github.com/LakshmiSravyaVedantham/human-speak)

PRs welcome — especially on the scorer heuristics. There's a lot of room to improve signal detection without adding dependencies.
