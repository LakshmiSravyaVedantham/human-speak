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
   - `score`: ambiguity score (0.0-1.0)
   - `signals`: list of signals detected (run-on, filler-words, missing-subject)

2. Form ONE clear interpretation of what the user wants.
   Use signals as hints:
   - `run-on` -> they have multiple ideas, identify the primary one
   - `filler-words` -> casual phrasing, infer the core request
   - `missing-subject` -> they told you what to do but not what to do it to -- infer from context

3. Ask for confirmation. Format exactly:
   > "I think you're asking me to [specific action]. Is that right?"

4. Wait for response:
   - **Yes / affirmative** -> proceed with interpreted action
   - **Correction** -> re-interpret, confirm once more, then act
   - **No response after one turn** -> proceed, prepend "Assuming you meant [X]..."

## Invariants

- Never act before confirmation
- Never rewrite or repeat back the user's raw message
- One interpretation per confirmation -- not a list of options
- Keep your interpretation sentence short (under 15 words)
