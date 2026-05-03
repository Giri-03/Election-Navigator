"""
Confidence Meter calculator — computes a weighted "voting readiness" score.

Weights (from design doc):
  critical = 3
  high     = 2
  medium   = 1

confidence_pct = (earned_weight / max_weight) * 100

Returns 0.0 when the step list is empty.
Result is always in [0.0, 100.0].
"""
from __future__ import annotations

from typing import List

from .models import Step, IMPORTANCE_WEIGHTS


def compute_confidence(steps: List[Step]) -> float:
    """
    Return a weighted readiness score as a percentage in [0.0, 100.0].
    Only steps with status 'done' contribute to the earned weight.
    """
    if not steps:
        return 0.0

    max_weight = sum(IMPORTANCE_WEIGHTS.get(s.importance, 1) for s in steps)
    if max_weight == 0:
        return 0.0

    earned = sum(
        IMPORTANCE_WEIGHTS.get(s.importance, 1)
        for s in steps
        if s.status == "done"
    )
    return round((earned / max_weight) * 100, 2)
