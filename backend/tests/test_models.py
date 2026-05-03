"""
Tests for data models — includes Property 12 (serialization round trip).
"""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from hypothesis import given, settings, strategies as st

from backend.models import (
    UserProfile,
    Step,
    TimelineMilestone,
    EligibilityResult,
    NavigatorResponse,
    UI_THEME,
    IMPORTANCE_WEIGHTS,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

VALID_STATES = ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Uttar Pradesh"]
IMPORTANCE_VALUES = ["critical", "high", "medium"]
LABEL_VALUES = ["registration", "verification", "polling", "result"]
STATUS_VALUES = ["pending", "done"]

st_nonempty_text = st.text(min_size=1, max_size=80).filter(lambda s: s.strip())

st_step = st.builds(
    Step,
    title=st_nonempty_text,
    description=st_nonempty_text,
    importance=st.sampled_from(IMPORTANCE_VALUES),
    action=st_nonempty_text,
    status=st.sampled_from(STATUS_VALUES),
)

st_milestone = st.builds(
    TimelineMilestone,
    label=st.sampled_from(LABEL_VALUES),
    date_range=st_nonempty_text,
    description=st_nonempty_text,
)

st_navigator_response = st.builds(
    NavigatorResponse,
    status=st.sampled_from(["profiling", "eligible", "not_eligible", "what_if", "complete"]),
    message=st_nonempty_text,
    next_step=st_nonempty_text,
    ui_component=st.sampled_from(["onboarding", "timeline", "checklist", "alert"]),
    steps=st.lists(st_step, min_size=0, max_size=6),
    timeline=st.lists(st_milestone, min_size=0, max_size=4),
    next_question=st.text(max_size=120),
    progress=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
    confidence=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
    ui_theme=st.just(dict(UI_THEME)),
)


# ---------------------------------------------------------------------------
# Property 12: Serialization round trip
# Feature: election-navigator, Property 12: Serialization round trip
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(response=st_navigator_response)
def test_p12_serialization_round_trip(response: NavigatorResponse):
    """
    For any valid NavigatorResponse, serializing to JSON and deserializing back
    produces a dict that is deeply equal to the original.
    Validates: Requirements 7.1, 7.2, 7.3
    """
    original_dict = response.to_dict()
    json_str = response.to_json()
    restored_dict = json.loads(json_str)
    assert original_dict == restored_dict


# ---------------------------------------------------------------------------
# Unit tests for UserProfile
# ---------------------------------------------------------------------------

def test_user_profile_is_complete_when_all_fields_set():
    p = UserProfile(age=25, citizenship="indian", state="Maharashtra",
                    first_time_voter=False, has_voter_id=True)
    assert p.is_complete() is True


def test_user_profile_incomplete_when_any_field_none():
    p = UserProfile(age=25, citizenship="indian", state="Maharashtra",
                    first_time_voter=False, has_voter_id=None)
    assert p.is_complete() is False


def test_user_profile_round_trip_dict():
    p = UserProfile(age=30, citizenship="indian", state="Delhi",
                    first_time_voter=True, has_voter_id=False)
    assert UserProfile.from_dict(p.to_dict()) == p


def test_blank_profile_is_not_complete():
    assert UserProfile().is_complete() is False


# ---------------------------------------------------------------------------
# Unit tests for NavigatorResponse.from_dict
# ---------------------------------------------------------------------------

def test_navigator_response_from_dict_restores_steps():
    r = NavigatorResponse(
        status="eligible",
        message="You are eligible.",
        next_step="Check your enrollment.",
        ui_component="checklist",
        steps=[Step("Verify", "Check voter list.", "critical", "Visit voters.eci.gov.in")],
    )
    restored = NavigatorResponse.from_dict(r.to_dict())
    assert len(restored.steps) == 1
    assert restored.steps[0].title == "Verify"


def test_navigator_response_from_dict_restores_timeline():
    r = NavigatorResponse(
        status="eligible",
        message="ok",
        next_step="proceed",
        ui_component="timeline",
        timeline=[TimelineMilestone("registration", "Oct 1–15 (approx.)", "Register now")],
    )
    restored = NavigatorResponse.from_dict(r.to_dict())
    assert restored.timeline[0].label == "registration"
