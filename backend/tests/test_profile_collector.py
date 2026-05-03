"""
Tests for ProfileCollector — includes Property 1 (profile advances one field per turn).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from hypothesis import given, settings, strategies as st

from backend.models import UserProfile
from backend.profile_collector import (
    ProfileCollector,
    QUESTIONS,
    INDIAN_STATES,
    PROFILE_FIELD_COUNT,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

VALID_STATES = list(INDIAN_STATES.values())

st_valid_age = st.integers(min_value=1, max_value=150).map(str)
st_valid_citizenship = st.sampled_from(["yes", "no", "indian", "other"])
st_valid_state = st.sampled_from(VALID_STATES)
st_valid_bool = st.sampled_from(["yes", "no"])


def _profile_with_n_fields(n: int, draw) -> UserProfile:
    """Build a UserProfile with exactly n fields filled (in sequence)."""
    p = UserProfile()
    valid_inputs = [
        draw(st_valid_age),
        draw(st_valid_citizenship),
        draw(st_valid_state),
        draw(st_valid_bool),
        draw(st_valid_bool),
    ]
    for i in range(n):
        result = ProfileCollector.process(p, valid_inputs[i])
        assert result.error is None, f"Unexpected error at field {i}: {result.error}"
        p = result.profile
    return p


# ---------------------------------------------------------------------------
# Property 1: Profile collection advances exactly one field per turn
# Feature: election-navigator, Property 1: Profile collection advances exactly one field per turn
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(data=st.data())
def test_p1_profile_advances_one_field_per_turn(data):
    """
    For any incomplete profile, processing one valid response populates
    exactly one additional field and the next question matches the next
    unpopulated field in the fixed sequence.
    Validates: Requirements 1.1, 1.2, 1.3
    """
    # Pick a random number of already-filled fields (0 to 4 — not complete)
    n_filled = data.draw(st.integers(min_value=0, max_value=PROFILE_FIELD_COUNT - 1))
    profile_before = _profile_with_n_fields(n_filled, data.draw)

    # Count filled fields before
    fields_before = sum(
        1 for f in ("age", "citizenship", "state", "first_time_voter", "has_voter_id")
        if getattr(profile_before, f) is not None
    )
    assert fields_before == n_filled

    # Determine which field comes next and supply a valid answer
    next_q = ProfileCollector.next_question(profile_before)
    assert next_q is not None  # profile is not complete yet

    valid_answers = {
        "age": data.draw(st_valid_age),
        "citizenship": data.draw(st_valid_citizenship),
        "state": data.draw(st.sampled_from(VALID_STATES)),
        "first_time_voter": data.draw(st_valid_bool),
        "has_voter_id": data.draw(st_valid_bool),
    }
    answer = valid_answers[next_q["field"]]

    result = ProfileCollector.process(profile_before, answer)
    assert result.error is None

    # Exactly one more field should now be filled
    fields_after = sum(
        1 for f in ("age", "citizenship", "state", "first_time_voter", "has_voter_id")
        if getattr(result.profile, f) is not None
    )
    assert fields_after == n_filled + 1

    # next_question should correspond to the next unpopulated field
    if not result.profile_complete:
        expected_next = ProfileCollector.next_question(result.profile)
        assert result.next_question == expected_next["text"]


# ---------------------------------------------------------------------------
# Unit tests — age validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected_error", [
    ("0",   True),
    ("1",   False),
    ("17",  False),
    ("18",  False),
    ("150", False),
    ("151", True),
    ("abc", True),
    ("-5",  True),
])
def test_age_validation_boundaries(raw, expected_error):
    profile = UserProfile()
    result = ProfileCollector.process(profile, raw)
    if expected_error:
        assert result.error is not None
        assert result.profile.age is None
    else:
        assert result.error is None
        assert result.profile.age == int(raw)


# ---------------------------------------------------------------------------
# Unit tests — citizenship validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("yes", "indian"), ("y", "indian"), ("indian", "indian"), ("india", "indian"),
    ("no", "other"), ("n", "other"), ("foreign", "other"),
])
def test_citizenship_valid_inputs(raw, expected):
    profile = UserProfile(age=25)
    result = ProfileCollector.process(profile, raw)
    assert result.error is None
    assert result.profile.citizenship == expected


def test_citizenship_invalid_input():
    profile = UserProfile(age=25)
    result = ProfileCollector.process(profile, "maybe")
    assert result.error is not None
    assert result.profile.citizenship is None


# ---------------------------------------------------------------------------
# Unit tests — state validation
# ---------------------------------------------------------------------------

def test_state_valid_exact():
    profile = UserProfile(age=25, citizenship="indian")
    result = ProfileCollector.process(profile, "Maharashtra")
    assert result.error is None
    assert result.profile.state == "Maharashtra"


def test_state_case_insensitive():
    profile = UserProfile(age=25, citizenship="indian")
    result = ProfileCollector.process(profile, "maharashtra")
    assert result.error is None
    assert result.profile.state == "Maharashtra"


def test_state_invalid():
    profile = UserProfile(age=25, citizenship="indian")
    result = ProfileCollector.process(profile, "Narnia")
    assert result.error is not None
    assert result.profile.state is None


# ---------------------------------------------------------------------------
# Unit tests — boolean fields
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("yes", True), ("y", True), ("true", True), ("1", True),
    ("no", False), ("n", False), ("false", False), ("0", False),
])
def test_bool_valid_inputs(raw, expected):
    profile = UserProfile(age=25, citizenship="indian", state="Delhi")
    result = ProfileCollector.process(profile, raw)
    assert result.error is None
    assert result.profile.first_time_voter == expected


# ---------------------------------------------------------------------------
# Unit tests — complete profile flow
# ---------------------------------------------------------------------------

def test_full_profile_collection_sequence():
    profile = UserProfile()
    answers = ["25", "yes", "Maharashtra", "yes", "no"]
    for answer in answers:
        result = ProfileCollector.process(profile, answer)
        assert result.error is None, f"Unexpected error: {result.error}"
        profile = result.profile
    assert profile.is_complete()
    assert profile.age == 25
    assert profile.citizenship == "indian"
    assert profile.state == "Maharashtra"
    assert profile.first_time_voter is True
    assert profile.has_voter_id is False


def test_process_on_complete_profile_returns_complete():
    profile = UserProfile(age=25, citizenship="indian", state="Delhi",
                          first_time_voter=True, has_voter_id=False)
    result = ProfileCollector.process(profile, "anything")
    assert result.profile_complete is True
    assert result.next_question is None
