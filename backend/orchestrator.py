"""
Orchestrator — wires all backend modules together and assembles the full
NavigatorResponse dict for every /chat_flow request.

Pipeline:
  1. Load profile from session
  2. Detect what-if scenario in user input
  3. If what-if → return alert response
  4. If profile incomplete → collect next field, return onboarding response
  5. If profile complete → check eligibility
     a. Not eligible → return ineligibility response
     b. Eligible → generate checklist + timeline, return dashboard response
  6. Validate envelope completeness before returning (raises InvalidResponseError)
"""
from __future__ import annotations

from typing import List

from .models import NavigatorResponse, Step, TimelineMilestone, UI_THEME
from .session_manager import SessionStateManager
from .profile_collector import ProfileCollector, PROFILE_FIELD_COUNT
from .eligibility_checker import EligibilityChecker
from .checklist_generator import ChecklistGenerator
from .timeline_generator import TimelineGenerator
from .whatif_detector import WhatIfDetector
from .whatif_handler import WhatIfHandler
from .progress import compute_progress
from .confidence import compute_confidence

# Required top-level fields in the response envelope (Requirements 7.1, 7.4, 7.5)
REQUIRED_FIELDS = [
    "status", "message", "next_step", "ui_component",
    "steps", "timeline", "next_question", "progress", "confidence", "ui_theme",
]

# Fields that must be present but are allowed to be empty string
# (e.g. next_question is empty once the profile is complete)
NULLABLE_STRING_FIELDS = {"next_question"}

# Fields whose string value must be non-empty
NONEMPTY_STRING_FIELDS = {"status", "message", "next_step", "ui_component"}


class InvalidResponseError(Exception):
    """Raised when the assembled response is missing a required field."""
    pass


def _validate_envelope(d: dict) -> None:
    """Raise InvalidResponseError if any required field is absent or
    a non-nullable string field is an empty string."""
    for field in REQUIRED_FIELDS:
        if field not in d:
            raise InvalidResponseError(f"Missing required field: '{field}'")
        value = d[field]
        if field in NONEMPTY_STRING_FIELDS and isinstance(value, str) and value == "":
            raise InvalidResponseError(f"Required field '{field}' is an empty string")


class Orchestrator:

    @staticmethod
    def process(user_input: str, session_steps: List[dict] = None) -> dict:
        """
        Main entry point for /chat_flow.

        session_steps: list of step dicts from the client (with current status
        toggles), used to compute live progress/confidence. Pass [] or None
        on first call.

        Returns a validated NavigatorResponse dict.
        """
        session_steps = session_steps or []

        # ----------------------------------------------------------------
        # 1. Load profile
        # ----------------------------------------------------------------
        profile = SessionStateManager.get_profile()

        # ----------------------------------------------------------------
        # 2. What-if detection (takes priority over normal flow)
        # ----------------------------------------------------------------
        scenario = WhatIfDetector.detect(user_input)
        if scenario:
            recovery = WhatIfHandler.get_recovery_steps(scenario)
            message = WhatIfHandler.get_message(scenario)
            # Convert recovery steps to Step objects for uniform rendering
            recovery_steps = [
                Step(
                    title=f"Recovery Step {i + 1}",
                    description=text[:120],
                    importance="high",
                    action=text,
                    status="pending",
                )
                for i, text in enumerate(recovery)
            ]
            response = NavigatorResponse(
                status="what_if",
                message=message,
                next_step="Follow the recovery steps below to resolve your situation.",
                ui_component="alert",
                steps=recovery_steps,
                timeline=[],
                next_question="",
                progress=0.0,
                confidence=0.0,
                ui_theme=dict(UI_THEME),
            )
            d = response.to_dict()
            _validate_envelope(d)
            return d

        # ----------------------------------------------------------------
        # 3. Profile collection
        # ----------------------------------------------------------------
        if not profile.is_complete():
            result = ProfileCollector.process(profile, user_input)
            SessionStateManager.save_profile(result.profile)

            # Count filled fields for onboarding progress indicator
            filled = sum(
                1 for f in ("age", "citizenship", "state", "first_time_voter", "has_voter_id")
                if getattr(result.profile, f) is not None
            )
            onboarding_progress = round((filled / PROFILE_FIELD_COUNT) * 100, 2)

            if result.error:
                # Validation failed — re-ask same question
                response = NavigatorResponse(
                    status="profiling",
                    message=result.error,
                    next_step=result.next_question or "Please answer the question above.",
                    ui_component="onboarding",
                    steps=[],
                    timeline=[],
                    next_question=result.next_question or "",
                    progress=onboarding_progress,
                    confidence=0.0,
                    ui_theme=dict(UI_THEME),
                )
            elif result.profile_complete:
                # Profile just completed — fall through to eligibility below
                # (handled in section 4 by re-checking is_complete)
                pass
            else:
                response = NavigatorResponse(
                    status="profiling",
                    message="Got it. One more question.",
                    next_step=result.next_question or "",
                    ui_component="onboarding",
                    steps=[],
                    timeline=[],
                    next_question=result.next_question or "",
                    progress=onboarding_progress,
                    confidence=0.0,
                    ui_theme=dict(UI_THEME),
                )
                d = response.to_dict()
                _validate_envelope(d)
                return d

            if not result.profile_complete:
                d = response.to_dict()
                _validate_envelope(d)
                return d

            # Profile is now complete — reload and continue to eligibility
            profile = SessionStateManager.get_profile()

        # ----------------------------------------------------------------
        # 4. Eligibility check
        # ----------------------------------------------------------------
        eligibility = EligibilityChecker.check(profile)

        if eligibility.status == "not_eligible":
            recovery_steps = [
                Step(
                    title=f"Next Step {i + 1}",
                    description=text[:120],
                    importance="high",
                    action=text,
                    status="pending",
                )
                for i, text in enumerate(eligibility.recovery_steps)
            ]
            response = NavigatorResponse(
                status="not_eligible",
                message=eligibility.reason or "You are not eligible to vote at this time.",
                next_step=eligibility.recovery_steps[0] if eligibility.recovery_steps else "Contact your local ERO.",
                ui_component="alert",
                steps=recovery_steps,
                timeline=[],
                next_question="",
                progress=0.0,
                confidence=0.0,
                ui_theme=dict(UI_THEME),
            )
            d = response.to_dict()
            _validate_envelope(d)
            return d

        # ----------------------------------------------------------------
        # 5. Eligible — generate checklist + timeline
        # ----------------------------------------------------------------
        checklist = ChecklistGenerator.generate(profile)
        timeline = TimelineGenerator.generate(profile.state or "")

        # Apply any status updates from the client-side session_steps
        status_map = {s["title"]: s.get("status", "pending") for s in session_steps}
        for step in checklist:
            if step.title in status_map:
                step.status = status_map[step.title]

        progress = compute_progress(checklist)
        confidence = compute_confidence(checklist)

        all_done = all(s.status == "done" for s in checklist)
        status = "complete" if all_done else "eligible"

        response = NavigatorResponse(
            status=status,
            message=(
                "You are eligible to vote! Here is your personalised checklist."
                if status == "eligible"
                else "You have completed all steps. You are ready to vote!"
            ),
            next_step=(
                next((s.action for s in checklist if s.status == "pending"), "All steps complete!")
            ),
            ui_component="checklist",
            steps=checklist,
            timeline=timeline,
            next_question="",
            progress=progress,
            confidence=confidence,
            ui_theme=dict(UI_THEME),
        )
        d = response.to_dict()
        _validate_envelope(d)
        return d
