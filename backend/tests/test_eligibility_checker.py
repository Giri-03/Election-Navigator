"""
Tests for EligibilityChecker — includes:
  Property 2: Age boundary eligibility
  Property 3: Ineligibility always produces non-empty reason and recovery
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from hypothesis import given, settings, strategies as st

from backend.models import UserProfile
from backend.eligibility_checker import EligibilityChecker
from backend.profile_collector import INDIAN_STATES

VALID_STATES = list(INDIAN_STATES.values())

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

st_underage_profile = st.builds(
    UserProfile,
    age=st.integers(min_value=1, max_value=17),
    citizenship=st.just("indian"),
    state=st_valid_state,
    first_time_voter=st.booleans(),
    has_voter_id=st.booleans(),
)

st_noncitizen_profile = st.builds(
    UserProfile,
    age=st.integers(min_value=18, max_value=150),
    citizenship=st.just("other"),
    state=st_valid_state,
    first_time_voter=st.booleans(),
    has_voter_id=st.booleans(),
)

st_ineligible_profile = st.one_of(st_underage_profile, st_noncitizen_profile)


# ---------------------------------------------------------------------------
# Property 2: Age boundary eligibility
# Feature: election-navigator, Property 2: Age boundary eligibility
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(profile=st_eligible_profile)
def test_p2_eligible_when_age_18_or_above(profile: UserProfile):
    """
    For any profile where age >= 18, citizenship is 'indian', and state is valid,
    the eligibility result SHALL be 'eligible'.
    Validates: Requirements 2.1, 2.4
    """
    result = EligibilityChecker.check(profile)
    assert result.status == "eligible"


@settings(max_examples=100)
@given(profile=st_underage_profile)
def test_p2_not_eligible_when_age_below_18(profile: UserProfile):
    """
    For any profile where age <= 17, the result SHALL be 'not_eligible'.
    Validates: Requirements 2.1, 2.4
    """
    result = EligibilityChecker.check(profile)
    assert result.status == "not_eligible"


# ---------------------------------------------------------------------------
# Property 3: Ineligibility always produces non-empty reason and recovery >= 1
# Feature: election-navigator, Property 3: Ineligibility always produces non-empty reason and recovery
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(profile=st_ineligible_profile)
def test_p3_ineligible_has_reason_and_recovery(profile: UserProfile):
    """
    For any profile that produces 'not_eligible', the response SHALL contain
    a non-empty reason string and recovery_steps with length >= 1.
    Validates: Requirements 2.3
    """
    result = EligibilityChecker.check(profile)
    assert result.status == "not_eligible"
    assert result.reason is not None
    assert len(result.reason.strip()) > 0
    assert len(result.recovery_steps) >= 1
    for step in result.recovery_steps:
        assert len(step.strip()) > 0


# ---------------------------------------------------------------------------
# Unit tests — all four eligibility rule combinations
# ---------------------------------------------------------------------------

def test_eligible_standard():
    p = UserProfile(age=25, citizenship="indian", state="Maharashtra",
                    first_time_voter=False, has_voter_id=True)
    r = EligibilityChecker.check(p)
    assert r.status == "eligible"
    assert r.reason is None
    assert r.recovery_steps == []


def test_eligible_exactly_18():
    """Age exactly 18 must be eligible (Requirement 2.4)."""
    p = UserProfile(age=18, citizenship="indian", state="Delhi",
                    first_time_voter=True, has_voter_id=False)
    r = EligibilityChecker.check(p)
    assert r.status == "eligible"


def test_not_eligible_underage_17():
    p = UserProfile(age=17, citizenship="indian", state="Karnataka",
                    first_time_voter=True, has_voter_id=False)
    r = EligibilityChecker.check(p)
    assert r.status == "not_eligible"
    assert "18" in r.reason


def test_not_eligible_non_citizen():
    """Non-Indian citizenship → not_eligible with ECI NRI guidance (Req 2.5)."""
    p = UserProfile(age=30, citizenship="other", state="Tamil Nadu",
                    first_time_voter=False, has_voter_id=False)
    r = EligibilityChecker.check(p)
    assert r.status == "not_eligible"
    assert any("voters.eci.gov.in" in step for step in r.recovery_steps)


def test_not_eligible_invalid_state():
    p = UserProfile(age=25, citizenship="indian", state="Narnia",
                    first_time_voter=False, has_voter_id=True)
    r = EligibilityChecker.check(p)
    assert r.status == "not_eligible"


def test_not_eligible_age_none():
    p = UserProfile(age=None, citizenship="indian", state="Delhi",
                    first_time_voter=False, has_voter_id=True)
    r = EligibilityChecker.check(p)
    assert r.status == "not_eligible"
