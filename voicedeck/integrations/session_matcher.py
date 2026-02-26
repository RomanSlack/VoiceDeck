"""Fuzzy matching of spoken session names against active claude-grid sessions."""

import difflib
from dataclasses import dataclass
from typing import Optional

from .claude_grid import SessionInfo


# Common filler words to strip from the start of transcripts
FILLER_WORDS = {"um", "uh", "so", "okay", "ok", "like", "well", "hey", "ah"}


@dataclass
class MatchResult:
    """Result of matching a transcript to a session."""
    session: SessionInfo
    command_text: str
    confidence: float


class SessionMatcher:
    """Matches spoken text to claude-grid session names."""

    def __init__(self, min_confidence: float = 0.8):
        self.min_confidence = min_confidence
        self._sessions: list[SessionInfo] = []

    def update_sessions(self, sessions: list[SessionInfo]) -> None:
        """Refresh the list of known sessions."""
        self._sessions = list(sessions)

    def match(self, transcript: str) -> Optional[MatchResult]:
        """Match a transcript to a session.

        Strips filler words, takes the first N words (where N matches
        session name word count), and fuzzy-matches against known sessions.

        Returns MatchResult if confidence > threshold, else None.
        """
        if not self._sessions or not transcript.strip():
            return None

        words = transcript.strip().split()

        # Strip leading filler words
        while words and words[0].lower().rstrip(".,!?") in FILLER_WORDS:
            words.pop(0)

        if not words:
            return None

        best_match: Optional[MatchResult] = None
        best_confidence = 0.0

        for session in self._sessions:
            n = len(session.words)
            if len(words) < n:
                continue

            # Take first N words as the potential session name
            candidate_words = [w.lower().rstrip(".,!?") for w in words[:n]]
            candidate = " ".join(candidate_words)
            target = " ".join(session.words)

            # Compare using SequenceMatcher
            confidence = difflib.SequenceMatcher(
                None, candidate, target
            ).ratio()

            if confidence > best_confidence:
                best_confidence = confidence
                remaining = " ".join(words[n:]).strip()
                best_match = MatchResult(
                    session=session,
                    command_text=remaining,
                    confidence=confidence,
                )

        if best_match and best_match.confidence >= self.min_confidence:
            return best_match

        return None
