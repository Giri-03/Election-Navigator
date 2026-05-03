"""
Tests for Orchestrator and Response Builder — includes:
  Property 9:  JSON response envelope always contains all required top-level fields
  Property 10: UI theme never uses forbidden fonts
  Property 11: UI theme layout_style never specifies a generic layout
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import patch

from backend.orchestrator import Orchestrator, InvalidResponseError, REQUIRED_FIELDS, NULLABLE_STRING_FIELDS
from backend.models import UserProfile, UI_THEME
from backend.session_manager import SessionStateManager

VALID_STATES = ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Uttar Pradesh"]

FORBIDDEN_FONTS = {"Inter", "Arial", "Roboto", "system-ui", "sans-serif", "serif"}
FORBIDDEN_LAYOUT_SUBSTRINGS = ["dashboard", "card grid", "bootstrap", "symmetric"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_complete_profile(ftv=False, hid=True, state="Maharashtra") -> UserProfile:
    return UserProfile(age=25, citizenship="indian", state=state,
                       first_time_voter=ftv, has_voter_id=hid)


def _run_with_profile(profile: UserProfile, message: str = "hello") -> dict:
    """Run orchestrator with a pre-set profile (bypasses session)."""
    with patch.object(SessionStateManager, "get_profile", return_value=profile), \
         patch.object(SessionStateManager, "save_profile"):
        return Orchestrator.process(message)


# ---------------------------------------------------------------------------
# Property 9: JSON response envelope always contains all required top-level fields
# Feature: election-navigator, Property 9: JSON response envelope always contains all required top-level fields
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    ftv=st.booleans(),
    hid=st.booleans(),
    state=st.sampled_from(VALID_STATES),
)
def test_p9_envelope_has_all_required_fields(ftv, hid, state):
    """
    For any eligible profile, the orchestrator response SHALL contain
    non-empty values for all required top-level fields.
    Validates: Requirements 7.1, 7.4, 7.5
    """
    profile = _make_complete_profile(ftv=ftv, hid=hid, state=state)
    result = _run_with_profile(profile)

    for field in REQUIRED_FIELDS:
        assert field in result, f"Missing field: '{field}'"
        value = result[field]
        if isinstance(value, str) and field not in NULLABLE_STRING_FIELDS:
            assert value != "", f"Field '{field}' is an empty string"


# ---------------------------------------------------------------------------
# Property 10: UI theme never uses forbidden fonts
# Feature: election-navigator, Property 10: UI theme never uses forbidden fonts
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    ftv=st.booleans(),
    hid=st.booleans(),
    state=st.sampled_from(VALID_STATES),
)
def test_p10_ui_theme_no_forbidden_fonts(ftv, hid, state):
    """
    For any generated ui_theme, heading and body fonts SHALL NOT be
    Inter, Arial, Roboto, or system-default fonts.
    Validates: Requirements 6.2
    """
    profile = _make_complete_profile(ftv=ftv, hid=hid, state=state)
    result = _run_with_profile(profile)

    fonts = result["ui_theme"]["fonts"]
    assert fonts["heading"] not in FORBIDDEN_FONTS, \
        f"Forbidden heading font: '{fonts['heading']}'"
    assert fonts["body"] not in FORBIDDEN_FONTS, \
        f"Forbidden body font: '{fonts['body']}'"


# ---------------------------------------------------------------------------
# Property 11: UI theme layout_style never specifies a generic layout
# Feature: election-navigator, Property 11: UI theme layout_style never specifies a generic layout
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    ftv=st.booleans(),
    hid=st.booleans(),
    state=st.sampled_from(VALID_STATES),
)
def test_p11_ui_theme_no_generic_layout(ftv, hid, state):
    """
    For any generated ui_theme, layout_style SHALL NOT contain
    'dashboard', 'card grid', 'bootstrap', or 'symmetric'.
    Validates: Requirements 6.4
    """
    profile = _make_complete_profile(ftv=ftv, hid=hid, state=state)
    result = _run_with_profile(profile)

    layout = result["ui_theme"]["layout_style"].lower()
    for forbidden in FORBIDDEN_LAYOUT_SUBSTRINGS:
        assert forbidden not in layout, \
            f"Forbidden layout substring '{forbidden}' found in: '{layout}'"


# ---------------------------------------------------------------------------
# Unit tests — orchestrator pipeline paths
# ---------------------------------------------------------------------------

def test_eligible_response_has_steps_and_timeline():
    profile = _make_complete_profile(ftv=False, hid=True)
    result = _run_with_profile(profile)
    assert result["status"] in ("eligible", "complete")
    assert len(result["steps"]) > 0
    assert len(result["timeline"]) == 4


def test_not_eligible_underage_returns_alert():
    profile = UserProfile(age=16, citizenship="indian", state="Delhi",
                          first_time_voter=True, has_voter_id=False)
    result = _run_with_profile(profile)
    assert result["status"] == "not_eligible"
    assert result["ui_component"] == "alert"
    assert len(result["steps"]) > 0  # recovery steps


def test_not_eligible_non_citizen_returns_alert():
    profile = UserProfile(age=25, citizenship="other", state="Delhi",
                          first_time_voter=False, has_voter_id=False)
    result = _run_with_profile(profile)
    assert result["status"] == "not_eligible"


def test_whatif_input_returns_what_if_status():
    profile = _make_complete_profile()
    result = _run_with_profile(profile, message="I lost my voter id")
    assert result["status"] == "what_if"
    assert result["ui_component"] == "alert"
    assert len(result["steps"]) >= 2


def test_profiling_incomplete_profile_returns_next_question():
    blank = UserProfile()
    with patch.object(SessionStateManager, "get_profile", return_value=blank), \
         patch.object(SessionStateManager, "save_profile"):
        result = Orchestrator.process("25")  # answer to age question
    assert result["status"] == "profiling"
    assert result["next_question"] != ""


def test_invalid_response_error_raised_on_missing_field():
    """InvalidResponseError is raised if a required field is missing."""
    from backend.orchestrator import _validate_envelope
    with pytest.raises(InvalidResponseError, match="Missing required field"):
        _validate_envelope({"status": "eligible"})  # missing most fields


def test_invalid_response_error_raised_on_empty_string():
    from backend.orchestrator import _validate_envelope, NONEMPTY_STRING_FIELDS
    envelope = {f: "ok" for f in REQUIRED_FIELDS}
    envelope["steps"] = []
    envelope["timeline"] = []
    envelope["progress"] = 0.0
    envelope["confidence"] = 0.0
    envelope["ui_theme"] = {}
    envelope["next_question"] = ""  # allowed to be empty
    envelope["message"] = ""  # NOT allowed — must be non-empty
    with pytest.raises(InvalidResponseError, match="empty string"):
        _validate_envelope(envelope)


def test_progress_and_confidence_in_response():
    profile = _make_complete_profile(ftv=True, hid=False)
    result = _run_with_profile(profile)
    assert 0.0 <= result["progress"] <= 100.0
    assert 0.0 <= result["confidence"] <= 100.0


def test_ui_theme_fonts_are_sora_and_jetbrains():
    """Fixed theme must use Sora + JetBrains Mono as specified in design."""
    profile = _make_complete_profile()
    result = _run_with_profile(profile)
    assert result["ui_theme"]["fonts"]["heading"] == "Sora"
    assert result["ui_theme"]["fonts"]["body"] == "JetBrains Mono"
