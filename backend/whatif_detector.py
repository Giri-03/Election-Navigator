"""
What-If Detector — keyword-matches user input to a WhatIfScenario.
Returns None if no scenario is detected (standard flow continues).

Keyword table (from design doc):
  missed, deadline, late, expired        → missed_deadline
  lost, no id, misplaced                 → lost_id
  not on list, missing name, not found   → missing_from_voter_list
  moved, relocated, new address, shifted → relocated
"""
from __future__ import annotations

from typing import Optional

# Each entry: (scenario_key, list_of_keyword_phrases)
# Phrases are checked as substrings of the lowercased input.
# Order matters — first match wins.
_KEYWORD_MAP = [
    ("missed_deadline", [
        "missed deadline", "missed the deadline", "deadline passed",
        "deadline missed", "too late", "late to register", "expired",
        "registration closed", "missed registration",
    ]),
    ("lost_id", [
        "lost my voter id", "lost voter id", "lost id", "lost my id",
        "no voter id", "no id", "misplaced id", "misplaced voter",
        "misplaced my voter", "can't find my id", "cannot find my id",
    ]),
    ("missing_from_voter_list", [
        "not on the list", "not on list", "missing from list",
        "name not found", "name missing", "not in voter list",
        "not registered", "not found in roll", "missing name",
        "name not on", "not in the roll",
    ]),
    ("relocated", [
        "moved to", "i moved", "relocated", "new address",
        "shifted to", "transferred to", "changed address",
        "new constituency", "different constituency",
    ]),
]


class WhatIfDetector:

    @staticmethod
    def detect(user_input: str) -> Optional[str]:
        """
        Return the matching WhatIfScenario string, or None if no match.
        Matching is case-insensitive substring search.
        """
        normalized = user_input.lower().strip()
        for scenario, phrases in _KEYWORD_MAP:
            for phrase in phrases:
                if phrase in normalized:
                    return scenario
        return None
