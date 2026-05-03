"""
Profile Collector — returns the next unanswered profile question and
validates/stores each answer in the fixed collection sequence:
  age → citizenship → state → first_time_voter → has_voter_id
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .models import UserProfile

# ---------------------------------------------------------------------------
# Known Indian states and union territories
# ---------------------------------------------------------------------------

INDIAN_STATES = {
    s.lower(): s
    for s in [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
        "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
        "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
        "West Bengal",
        # Union Territories
        "Andaman and Nicobar Islands", "Chandigarh",
        "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
        "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
    ]
}

# Fixed question sequence — one entry per profile field
QUESTIONS = [
    {
        "field": "age",
        "text": "How old are you?",
        "hint": "Enter your age as a number (e.g. 25).",
        "input_type": "number",
    },
    {
        "field": "citizenship",
        "text": "Are you an Indian citizen?",
        "hint": "Reply 'yes' or 'no'.",
        "input_type": "yesno",
    },
    {
        "field": "state",
        "text": "Which state or union territory are you registered in (or plan to register in)?",
        "hint": "Enter the full state name (e.g. Maharashtra, Delhi).",
        "input_type": "text",
    },
    {
        "field": "first_time_voter",
        "text": "Is this your first time voting?",
        "hint": "Reply 'yes' or 'no'.",
        "input_type": "yesno",
    },
    {
        "field": "has_voter_id",
        "text": "Do you already have a Voter ID card (EPIC)?",
        "hint": "Reply 'yes' or 'no'.",
        "input_type": "yesno",
    },
]

# Total number of profile fields (used for progress calculation)
PROFILE_FIELD_COUNT = len(QUESTIONS)


@dataclass
class CollectorResult:
    """Returned by ProfileCollector.process()."""
    profile: UserProfile
    next_question: Optional[str]       # None when profile is complete
    next_hint: Optional[str]
    next_input_type: Optional[str]
    error: Optional[str]               # validation error message, if any
    profile_complete: bool


class ProfileCollector:
    """
    Stateless helper — all state lives in the UserProfile passed in/out.
    """

    @staticmethod
    def next_question(profile: UserProfile) -> Optional[dict]:
        """Return the next unanswered question dict, or None if complete."""
        for q in QUESTIONS:
            if getattr(profile, q["field"]) is None:
                return q
        return None

    @staticmethod
    def process(profile: UserProfile, raw_input: str) -> CollectorResult:
        """
        Validate raw_input for the current unanswered field, store it in
        profile, and return the updated profile plus the next question.

        Returns a CollectorResult with error set if validation fails
        (profile is NOT updated in that case).
        """
        q = ProfileCollector.next_question(profile)
        if q is None:
            # Profile already complete — nothing to do
            return CollectorResult(
                profile=profile,
                next_question=None,
                next_hint=None,
                next_input_type=None,
                error=None,
                profile_complete=True,
            )

        value, error = ProfileCollector._validate(q, raw_input.strip())
        if error:
            return CollectorResult(
                profile=profile,
                next_question=q["text"],
                next_hint=q["hint"],
                next_input_type=q["input_type"],
                error=error,
                profile_complete=False,
            )

        # Store validated value
        updated = UserProfile(
            age=profile.age,
            citizenship=profile.citizenship,
            state=profile.state,
            first_time_voter=profile.first_time_voter,
            has_voter_id=profile.has_voter_id,
        )
        setattr(updated, q["field"], value)

        next_q = ProfileCollector.next_question(updated)
        return CollectorResult(
            profile=updated,
            next_question=next_q["text"] if next_q else None,
            next_hint=next_q["hint"] if next_q else None,
            next_input_type=next_q["input_type"] if next_q else None,
            error=None,
            profile_complete=next_q is None,
        )

    # ------------------------------------------------------------------
    # Internal validators
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(question: dict, raw: str) -> Tuple[object, Optional[str]]:
        field = question["field"]

        if field == "age":
            return ProfileCollector._validate_age(raw)

        if field == "citizenship":
            return ProfileCollector._validate_yesno_citizenship(raw)

        if field == "state":
            return ProfileCollector._validate_state(raw)

        if field in ("first_time_voter", "has_voter_id"):
            return ProfileCollector._validate_bool(raw)

        return None, f"Unknown field: {field}"

    @staticmethod
    def _validate_age(raw: str) -> Tuple[Optional[int], Optional[str]]:
        try:
            age = int(raw)
        except ValueError:
            return None, "Please enter your age as a whole number (e.g. 25)."
        if age < 1 or age > 150:
            return None, f"Age must be between 1 and 150. You entered {age}."
        return age, None

    @staticmethod
    def _validate_yesno_citizenship(raw: str) -> Tuple[Optional[str], Optional[str]]:
        normalized = raw.lower()
        if normalized in ("yes", "y", "indian", "india"):
            return "indian", None
        if normalized in ("no", "n", "other", "foreign"):
            return "other", None
        return None, "Please reply 'yes' if you are an Indian citizen, or 'no' if not."

    @staticmethod
    def _validate_state(raw: str) -> Tuple[Optional[str], Optional[str]]:
        key = raw.lower().strip()
        canonical = INDIAN_STATES.get(key)
        if canonical:
            return canonical, None
        # Partial match fallback
        matches = [v for k, v in INDIAN_STATES.items() if key in k]
        if len(matches) == 1:
            return matches[0], None
        hint = "Try the full name, e.g. Maharashtra, Delhi, Tamil Nadu."
        return None, f"'{raw}' is not a recognised Indian state or UT. {hint}"

    @staticmethod
    def _validate_bool(raw: str) -> Tuple[Optional[bool], Optional[str]]:
        normalized = raw.lower()
        if normalized in ("yes", "y", "true", "1"):
            return True, None
        if normalized in ("no", "n", "false", "0"):
            return False, None
        return None, "Please reply 'yes' or 'no'."
