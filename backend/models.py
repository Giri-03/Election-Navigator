"""
Data models for the Election Navigator Assistant.
All dataclasses are JSON-serializable via `to_dict()` methods.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import List, Literal, Optional

# ---------------------------------------------------------------------------
# Core domain types
# ---------------------------------------------------------------------------

WhatIfScenario = Literal[
    "missed_deadline",
    "lost_id",
    "missing_from_voter_list",
    "relocated",
]

IMPORTANCE_WEIGHTS = {"critical": 3, "high": 2, "medium": 1}


@dataclass
class UserProfile:
    age: Optional[int] = None
    citizenship: Optional[str] = None       # "indian" | "other"
    state: Optional[str] = None
    first_time_voter: Optional[bool] = None
    has_voter_id: Optional[bool] = None

    def is_complete(self) -> bool:
        return all(
            v is not None
            for v in (
                self.age,
                self.citizenship,
                self.state,
                self.first_time_voter,
                self.has_voter_id,
            )
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "UserProfile":
        return UserProfile(
            age=d.get("age"),
            citizenship=d.get("citizenship"),
            state=d.get("state"),
            first_time_voter=d.get("first_time_voter"),
            has_voter_id=d.get("has_voter_id"),
        )


@dataclass
class Step:
    title: str
    description: str        # max 2 lines
    importance: str         # "critical" | "high" | "medium"
    action: str             # imperative, actionable
    status: str = "pending" # "pending" | "done"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TimelineMilestone:
    label: str          # "registration" | "verification" | "polling" | "result"
    date_range: str     # e.g. "Oct 1–15 (approx.)"
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EligibilityResult:
    status: str                         # "eligible" | "not_eligible"
    reason: Optional[str] = None        # populated only when not_eligible
    recovery_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Fixed UI theme (single design direction per spec)
# ---------------------------------------------------------------------------

UI_THEME: dict = {
    "fonts": {
        "heading": "Sora",
        "body": "JetBrains Mono",
    },
    "colors": {
        "bg_primary": "#0a0f1c",
        "bg_secondary": "#111827",
        "accent_main": "#00f5d4",
        "accent_alert": "#ff4d6d",
        "text_primary": "#e5e7eb",
        "text_dim": "#9ca3af",
    },
    "layout_style": "split — left status panel, right content panel with timeline above checklist",
    "animation_style": "staggered load reveal, glow pulse on step completion",
    "background_style": "layered dark gradient with subtle grid overlay and radial glow at top-center",
}


@dataclass
class NavigatorResponse:
    status: str                                     # profiling | eligible | not_eligible | what_if | complete
    message: str
    next_step: str
    ui_component: str                               # onboarding | timeline | checklist | alert
    steps: List[Step] = field(default_factory=list)
    timeline: List[TimelineMilestone] = field(default_factory=list)
    next_question: str = ""
    progress: float = 0.0
    confidence: float = 0.0
    ui_theme: dict = field(default_factory=lambda: dict(UI_THEME))

    def to_dict(self) -> dict:
        d = {
            "status": self.status,
            "message": self.message,
            "next_step": self.next_step,
            "ui_component": self.ui_component,
            "steps": [s.to_dict() for s in self.steps],
            "timeline": [t.to_dict() for t in self.timeline],
            "next_question": self.next_question,
            "progress": self.progress,
            "confidence": self.confidence,
            "ui_theme": self.ui_theme,
        }
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @staticmethod
    def from_dict(d: dict) -> "NavigatorResponse":
        steps = [
            Step(**s) if isinstance(s, dict) else s
            for s in d.get("steps", [])
        ]
        timeline = [
            TimelineMilestone(**t) if isinstance(t, dict) else t
            for t in d.get("timeline", [])
        ]
        return NavigatorResponse(
            status=d["status"],
            message=d["message"],
            next_step=d["next_step"],
            ui_component=d["ui_component"],
            steps=steps,
            timeline=timeline,
            next_question=d.get("next_question", ""),
            progress=d.get("progress", 0.0),
            confidence=d.get("confidence", 0.0),
            ui_theme=d.get("ui_theme", dict(UI_THEME)),
        )
