"""
Tests for ChecklistGenerator — includes:
  Property 4: Checklist steps always contain all four required fields
  Property 5: First-time voter without ID receives registration step first
  Property 6: Existing voter ID holder skips registration steps
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from hypothesis import given, settings, strategies as st

from backend.models import UserProfile
from backend.checklist_generator import ChecklistGenerator, ECI_PORTAL
from backend.profile_collector import INDIAN_STATES

VALID_STATES = list(INDIAN_STATES.values())

REGISTRATION_KEYWORDS = ("register", "registration", "form 6", "new voter")

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

st_valid_state = st.sampled_from(VALID_STATES)

st_eligible_profile = st.builds(
    UserProfile,
    age=st.integers(min_value=18, max_value=150),
    citizenship=st.just("indian"),
    state=st_valid_state,
    first_time_voter=st.booleans(),
    has_voter_id=st.booleans(),
)

st_ftv_no_id = st.builds(
    UserProfile,
    age=st.integers(min_value=18, max_value=150),
    citizenship=st.just("indian"),
    state=st_valid_state,
    first_time_voter=st.just(True),
    has_voter_id=st.just(False),
)

st_has_id = st.builds(
    UserProfile,
    age=st.integers(min_value=18, max_value=150),
    citizenship=st.just("indian"),
    state=st_valid_state,
    first_time_voter=st.booleans(),
    has_voter_id=st.just(True),
)


def _references_registration(step) -> bool:
    combined = (step.title + " " + step.action).lower()
    return any(kw in combined for kw in REGISTRATION_KEYWORDS)


# ---------------------------------------------------------------------------
# Property 4: Checklist steps always contain all four required fields
# Feature: election-navigator, Property 4: Checklist steps always contain all four required fields
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(profile=st_eligible_profile)
def test_p4_all_steps_have_required_fields(profile: UserProfile):
    """
    For any eligible profile, every step SHALL have non-empty title,
    description, importance, and action.
    Validates: Requirements 3.1
    """
    steps = ChecklistGenerator.generate(profile)
    assert len(steps) > 0
    for step in steps:
        assert step.title.strip(), "title must be non-empty"
        assert step.description.strip(), "description must be non-empty"
        assert step.importance in ("critical", "high", "medium"), \
            f"importance must be critical/high/medium, got '{step.importance}'"
        assert step.action.strip(), "action must be non-empty"


# ---------------------------------------------------------------------------
# Property 5: First-time voter without ID receives registration step first
# Feature: election-navigator, Property 5: First-time voter without ID receives registration step first
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(profile=st_ftv_no_id)
def test_p5_first_time_no_id_starts_with_registration(profile: UserProfile):
    """
    For any eligible profile where first_time_voter=True and has_voter_id=False,
    the first step SHALL reference voter registration.
    Validates: Requirements 3.3
    """
    steps = ChecklistGenerator.generate(profile)
    assert len(steps) > 0
    assert _references_registration(steps[0]), (
        f"Expected first step to reference registration, got: '{steps[0].title}'"
    )


# ---------------------------------------------------------------------------
# Property 6: Existing voter ID holder skips registration steps
# Feature: election-navigator, Property 6: Existing voter ID holder skips registration steps
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(profile=st_has_id)
def test_p6_has_id_no_registration_steps(profile: UserProfile):
    """
    For any eligible profile where has_voter_id=True, the checklist SHALL NOT
    contain any step referencing voter registration or ID application.
    Validates: Requirements 3.4
    """
    steps = ChecklistGenerator.generate(profile)
    for step in steps:
        assert not _references_registration(step), (
            f"Unexpected registration step for has_voter_id=True: '{step.title}'"
        )


# ---------------------------------------------------------------------------
# Unit tests — all four branching paths
# ---------------------------------------------------------------------------

def _make(ftv: bool, hid: bool, state: str = "Maharashtra") -> UserProfile:
    return UserProfile(age=25, citizenship="indian", state=state,
                       first_time_voter=ftv, has_voter_id=hid)


def test_branch_ftv_no_id_has_6_steps():
    steps = ChecklistGenerator.generate(_make(True, False))
    assert len(steps) == 6


def test_branch_ftv_has_id_has_4_steps():
    steps = ChecklistGenerator.generate(_make(True, True))
    assert len(steps) == 4


def test_branch_returning_no_id_has_5_steps():
    steps = ChecklistGenerator.generate(_make(False, False))
    assert len(steps) == 5


def test_branch_returning_has_id_has_4_steps():
    steps = ChecklistGenerator.generate(_make(False, True))
    assert len(steps) == 4


def test_eci_portal_referenced_in_every_checklist():
    """At least one step action must reference the ECI portal (Req 3.5, 8.2)."""
    for ftv in (True, False):
        for hid in (True, False):
            steps = ChecklistGenerator.generate(_make(ftv, hid))
            assert any(ECI_PORTAL in s.action for s in steps), (
                f"No ECI portal reference for ftv={ftv}, hid={hid}"
            )


def test_returning_voter_no_id_starts_with_apply_id():
    steps = ChecklistGenerator.generate(_make(False, False))
    assert "apply" in steps[0].title.lower() or "voter id" in steps[0].title.lower()


def test_state_name_appears_in_steps():
    steps = ChecklistGenerator.generate(_make(True, False, state="Kerala"))
    combined = " ".join(s.description for s in steps)
    assert "Kerala" in combined
