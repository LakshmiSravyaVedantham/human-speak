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
