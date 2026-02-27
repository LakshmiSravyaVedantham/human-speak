"""Ambiguity scorer for user messages.

Scores a message 0.0-1.0 for ambiguity using pure heuristics.
No external dependencies -- stdlib only.
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
    """Score a message for ambiguity. Returns float 0.0-1.0."""
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
