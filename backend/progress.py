"""
Progress calculator — computes journey completion percentage.

progress = (completed_steps / total_steps) * 100

Returns 0.0 when the step list is empty (no division by zero).
Result is always in [0.0, 100.0].
"""
from __future__ import annotations

from typing import List

from .models import Step


def compute_progress(steps: List[Step]) -> float:
    """
    Return the percentage of steps with status 'done'.
    Result is in [0.0, 100.0].
    """
    if not steps:
        return 0.0
    completed = sum(1 for s in steps if s.status == "done")
    return round((completed / len(steps)) * 100, 2)
