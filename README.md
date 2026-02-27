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
