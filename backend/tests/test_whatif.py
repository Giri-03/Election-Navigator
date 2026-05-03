"""
Tests for WhatIfDetector and WhatIfHandler — includes:
  Property 8: What-if handler always returns at least two recovery steps
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from hypothesis import given, settings, strategies as st

from backend.whatif_detector import WhatIfDetector
from backend.whatif_handler import WhatIfHandler

ALL_SCENARIOS = ["missed_deadline", "lost_id", "missing_from_voter_list", "relocated"]

# ---------------------------------------------------------------------------
# Property 8: What-if handler always returns at least two recovery steps
# Feature: election-navigator, Property 8: What-if handler always returns at least two recovery steps
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(scenario=st.sampled_from(ALL_SCENARIOS))
def test_p8_whatif_handler_returns_at_least_two_steps(scenario: str):
    """
    For any detected WhatIfScenario, the handler SHALL return a list of
    at least two recovery steps, each non-empty.
    Validates: Requirements 5.1, 5.2, 5.3, 5.4
    """
    steps = WhatIfHandler.get_recovery_steps(scenario)
    assert len(steps) >= 2, f"Expected ≥2 steps for '{scenario}', got {len(steps)}"
    for step in steps:
        assert step.strip(), f"Empty recovery step found for scenario '{scenario}'"


# ---------------------------------------------------------------------------
# Unit tests — WhatIfDetector keyword matching
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("I missed the deadline to register", "missed_deadline"),
    ("The registration deadline passed", "missed_deadline"),
    ("It's too late to register", "missed_deadline"),
    ("I lost my voter id", "lost_id"),
    ("I have no id", "lost_id"),
    ("I misplaced my voter id", "lost_id"),
    ("My name is not on the list", "missing_from_voter_list"),
    ("My name is missing from list", "missing_from_voter_list"),
    ("I am not registered", "missing_from_voter_list"),
    ("I moved to a new city", "relocated"),
    ("I relocated to Delhi", "relocated"),
    ("I have a new address", "relocated"),
    ("I shifted to Mumbai", "relocated"),
])
def test_detector_matches_known_phrases(text, expected):
    result = WhatIfDetector.detect(text)
    assert result == expected, f"Input: '{text}' → expected '{expected}', got '{result}'"


@pytest.mark.parametrize("text", [
    "I want to vote",
    "How do I register?",
    "What is my polling booth?",
    "Hello",
    "",
    "   ",
])
def test_detector_returns_none_for_non_whatif_input(text):
    result = WhatIfDetector.detect(text)
    assert result is None, f"Expected None for '{text}', got '{result}'"


def test_detector_is_case_insensitive():
    assert WhatIfDetector.detect("I LOST MY VOTER ID") == "lost_id"
    assert WhatIfDetector.detect("MISSED DEADLINE") == "missed_deadline"


# ---------------------------------------------------------------------------
# Unit tests — WhatIfHandler content
# ---------------------------------------------------------------------------

def test_all_scenarios_have_eci_reference():
    """Every scenario's recovery steps must reference ECI (Req 5.1–5.4)."""
    for scenario in ALL_SCENARIOS:
        steps = WhatIfHandler.get_recovery_steps(scenario)
        combined = " ".join(steps).lower()
        assert "eci" in combined or "voters.eci.gov.in" in combined or "1950" in combined, (
            f"No ECI reference found in steps for scenario '{scenario}'"
        )


def test_unknown_scenario_returns_empty_list():
    steps = WhatIfHandler.get_recovery_steps("unknown_scenario")
    assert steps == []


def test_handler_messages_are_non_empty():
    for scenario in ALL_SCENARIOS:
        msg = WhatIfHandler.get_message(scenario)
        assert msg.strip(), f"Empty message for scenario '{scenario}'"


@pytest.mark.parametrize("scenario", ALL_SCENARIOS)
def test_each_scenario_has_four_steps(scenario):
    """Each scenario has exactly 4 recovery steps in the current implementation."""
    steps = WhatIfHandler.get_recovery_steps(scenario)
    assert len(steps) == 4
