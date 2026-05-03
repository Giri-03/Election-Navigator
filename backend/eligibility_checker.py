"""
Eligibility Checker — evaluates a complete UserProfile and returns
an EligibilityResult with status, reason, and recovery steps.

Rules (from design doc):
  age < 18              → not_eligible (underage)
  citizenship != indian → not_eligible (non-citizen)
  state unrecognized    → not_eligible (invalid state — should not reach here
                          after ProfileCollector validation, but handled defensively)
  all conditions met    → eligible
"""
from __future__ import annotations

from .models import EligibilityResult, UserProfile
from .profile_collector import INDIAN_STATES


class EligibilityChecker:

    @staticmethod
    def check(profile: UserProfile) -> EligibilityResult:
        """
        Evaluate eligibility for the given profile.
        Returns EligibilityResult with status 'eligible' or 'not_eligible'.
        """
        # --- age check ---
        if profile.age is None or profile.age < 18:
            age_str = str(profile.age) if profile.age is not None else "unknown"
            return EligibilityResult(
                status="not_eligible",
                reason=(
                    f"You must be at least 18 years old to vote in India. "
                    f"Your age ({age_str}) does not meet this requirement."
                ),
                recovery_steps=[
                    "You will become eligible to vote once you turn 18.",
                    "Pre-register your details at voters.eci.gov.in so you are ready "
                    "when you become eligible.",
                    "Contact your local Electoral Registration Officer (ERO) for "
                    "information on upcoming registration drives.",
                ],
            )

        # --- citizenship check ---
        if profile.citizenship != "indian":
            return EligibilityResult(
                status="not_eligible",
                reason=(
                    "Only Indian citizens are eligible to vote in Indian elections. "
                    "Non-citizens and foreign nationals cannot be enrolled on the "
                    "electoral roll."
                ),
                recovery_steps=[
                    "If you are an Overseas Citizen of India (OCI) or Non-Resident "
                    "Indian (NRI), visit voters.eci.gov.in for NRI voter registration "
                    "guidelines under Section 20A of the Representation of the People "
                    "Act, 1950.",
                    "If you believe your citizenship status has changed, contact the "
                    "Ministry of Home Affairs or your nearest Indian consulate.",
                ],
            )

        # --- state check (defensive) ---
        if profile.state is None or profile.state.lower() not in INDIAN_STATES:
            return EligibilityResult(
                status="not_eligible",
                reason=(
                    f"The state '{profile.state}' is not a recognised Indian state "
                    f"or union territory."
                ),
                recovery_steps=[
                    "Re-enter your state using the full official name "
                    "(e.g. Maharashtra, Tamil Nadu, Delhi).",
                    "Visit voters.eci.gov.in to find your correct constituency.",
                ],
            )

        # --- all checks passed ---
        return EligibilityResult(
            status="eligible",
            reason=None,
            recovery_steps=[],
        )
