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
- Do not ask multiple clarifying questions -- one interpretation, one confirmation
- Do not change the user's actual request, only clarify it
