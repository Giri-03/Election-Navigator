"""
Tests for TimelineGenerator — includes:
  Property 7: Timeline always contains exactly four milestones in order
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from hypothesis import given, settings, strategies as st

from backend.timeline_generator import TimelineGenerator, MILESTONE_ORDER, APPROX_LABEL
from backend.profile_collector import INDIAN_STATES

VALID_STATES = list(INDIAN_STATES.values())

# ---------------------------------------------------------------------------
# Property 7: Timeline always contains exactly four milestones in order
# Feature: election-navigator, Property 7: Timeline always contains exactly four milestones in order
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(state=st.sampled_from(VALID_STATES))
def test_p7_timeline_has_four_milestones_in_order(state: str):
    """
    For any valid Indian state, the generated timeline SHALL contain exactly
    four entries with labels 'registration', 'verification', 'polling', 'result'
    in that order.
    Validates: Requirements 4.1
    """
    milestones = TimelineGenerator.generate(state)

    assert len(milestones) == 4, f"Expected 4 milestones, got {len(milestones)}"

    for i, milestone in enumerate(milestones):
        assert milestone.label == MILESTONE_ORDER[i], (
            f"Position {i}: expected '{MILESTONE_ORDER[i]}', got '{milestone.label}'"
        )


@settings(max_examples=20)
@given(state=st.text(min_size=1, max_size=30))
def test_p7_unknown_state_still_returns_four_milestones(state: str):
    """
    Even for unknown/arbitrary state strings, the fallback must still
    return exactly 4 milestones in the correct order.
    Validates: Requirements 4.1, 8.4
    """
    milestones = TimelineGenerator.generate(state)
    assert len(milestones) == 4
    for i, m in enumerate(milestones):
        assert m.label == MILESTONE_ORDER[i]


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_all_date_ranges_contain_approx_label():
    """All date_range values must contain the approx label (Req 4.2)."""
    for state in VALID_STATES:
        milestones = TimelineGenerator.generate(state)
        for m in milestones:
            assert APPROX_LABEL in m.date_range, (
                f"Missing approx label in {state} / {m.label}: '{m.date_range}'"
            )


def test_all_descriptions_non_empty():
    for state in VALID_STATES:
        milestones = TimelineGenerator.generate(state)
        for m in milestones:
            assert m.description.strip(), f"Empty description for {state}/{m.label}"


def test_known_state_maharashtra_has_specific_dates():
    milestones = TimelineGenerator.generate("Maharashtra")
    reg = milestones[0]
    assert "Sep" in reg.date_range or "Oct" in reg.date_range


def test_known_state_case_insensitive():
    lower = TimelineGenerator.generate("maharashtra")
    upper = TimelineGenerator.generate("Maharashtra")
    assert [m.label for m in lower] == [m.label for m in upper]


def test_unknown_state_falls_back_to_generic():
    milestones = TimelineGenerator.generate("Narnia")
    assert len(milestones) == 4
    # Generic fallback uses "Varies by state" for registration
    assert "Varies" in milestones[0].date_range or "varies" in milestones[0].date_range.lower()


def test_empty_state_falls_back_to_generic():
    milestones = TimelineGenerator.generate("")
    assert len(milestones) == 4


def test_milestone_labels_are_correct_strings():
    milestones = TimelineGenerator.generate("Delhi")
    labels = [m.label for m in milestones]
    assert labels == ["registration", "verification", "polling", "result"]
