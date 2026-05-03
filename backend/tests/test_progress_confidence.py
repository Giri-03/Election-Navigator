"""
Tests for progress and confidence calculators — includes:
  Property 13: Progress is bounded between 0 and 100
  Property 14: Confidence is bounded between 0 and 100
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from hypothesis import given, settings, strategies as st

from backend.models import Step, IMPORTANCE_WEIGHTS
from backend.progress import compute_progress
from backend.confidence import compute_confidence

IMPORTANCE_VALUES = list(IMPORTANCE_WEIGHTS.keys())  # critical, high, medium
STATUS_VALUES = ["pending", "done"]

st_nonempty_text = st.text(min_size=1, max_size=40).filter(lambda s: s.strip())

st_step = st.builds(
    Step,
    title=st_nonempty_text,
    description=st_nonempty_text,
    importance=st.sampled_from(IMPORTANCE_VALUES),
    action=st_nonempty_text,
    status=st.sampled_from(STATUS_VALUES),
)

st_step_list = st.lists(st_step, min_size=0, max_size=10)


# ---------------------------------------------------------------------------
# Property 13: Progress is bounded between 0 and 100
# Feature: election-navigator, Property 13: Progress is bounded between 0 and 100
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(steps=st_step_list)
def test_p13_progress_bounded_0_to_100(steps):
    """
    For any checklist state, the computed progress value SHALL be in [0, 100].
    Validates: Requirements — Progress Bar feature
    """
    result = compute_progress(steps)
    assert 0.0 <= result <= 100.0, f"Progress out of bounds: {result}"


# ---------------------------------------------------------------------------
# Property 14: Confidence is bounded between 0 and 100
# Feature: election-navigator, Property 14: Confidence is bounded between 0 and 100
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(steps=st_step_list)
def test_p14_confidence_bounded_0_to_100(steps):
    """
    For any checklist state, the computed confidence value SHALL be in [0, 100].
    Validates: Requirements — Confidence Meter feature
    """
    result = compute_confidence(steps)
    assert 0.0 <= result <= 100.0, f"Confidence out of bounds: {result}"


# ---------------------------------------------------------------------------
# Unit tests — progress
# ---------------------------------------------------------------------------

def _make_steps(statuses: list, importance: str = "high") -> list:
    return [
        Step(title=f"Step {i}", description="desc", importance=importance,
             action="act", status=s)
        for i, s in enumerate(statuses)
    ]


def test_progress_empty_list():
    assert compute_progress([]) == 0.0


def test_progress_all_pending():
    steps = _make_steps(["pending", "pending", "pending"])
    assert compute_progress(steps) == 0.0


def test_progress_all_done():
    steps = _make_steps(["done", "done", "done"])
    assert compute_progress(steps) == 100.0


def test_progress_half_done():
    steps = _make_steps(["done", "pending", "done", "pending"])
    assert compute_progress(steps) == 50.0


def test_progress_one_of_four():
    steps = _make_steps(["done", "pending", "pending", "pending"])
    assert compute_progress(steps) == 25.0


# ---------------------------------------------------------------------------
# Unit tests — confidence
# ---------------------------------------------------------------------------

def test_confidence_empty_list():
    assert compute_confidence([]) == 0.0


def test_confidence_all_pending():
    steps = _make_steps(["pending", "pending"], importance="critical")
    assert compute_confidence(steps) == 0.0


def test_confidence_all_done_same_weight():
    steps = _make_steps(["done", "done"], importance="medium")
    assert compute_confidence(steps) == 100.0


def test_confidence_mixed_weights():
    # critical(3) done + high(2) pending + medium(1) done
    # earned = 3 + 1 = 4, max = 3 + 2 + 1 = 6 → 66.67%
    steps = [
        Step("A", "d", "critical", "act", "done"),
        Step("B", "d", "high",     "act", "pending"),
        Step("C", "d", "medium",   "act", "done"),
    ]
    result = compute_confidence(steps)
    assert abs(result - 66.67) < 0.1


def test_confidence_only_critical_done():
    # critical(3) done + high(2) pending → earned=3, max=5 → 60%
    steps = [
        Step("A", "d", "critical", "act", "done"),
        Step("B", "d", "high",     "act", "pending"),
    ]
    result = compute_confidence(steps)
    assert abs(result - 60.0) < 0.1


def test_confidence_all_done_mixed_weights():
    steps = [
        Step("A", "d", "critical", "act", "done"),
        Step("B", "d", "high",     "act", "done"),
        Step("C", "d", "medium",   "act", "done"),
    ]
    assert compute_confidence(steps) == 100.0
