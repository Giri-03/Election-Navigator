"""
Checklist Generator — produces a personalized list of Step objects based on
the 2×2 branching logic (first_time_voter × has_voter_id).

Branching:
  first_time=True,  has_id=False → [register, apply_id, verify, booth, carry_id, vote]
  first_time=True,  has_id=True  → [verify, booth, carry_id, vote]
  first_time=False, has_id=False → [apply_id, verify, booth, carry_id, vote]
  first_time=False, has_id=True  → [verify, booth, carry_id, vote]

At least one step action references voters.eci.gov.in (Requirement 3.5, 8.2).
"""
from __future__ import annotations

from typing import List

from .models import Step, UserProfile

ECI_PORTAL = "voters.eci.gov.in"

# ---------------------------------------------------------------------------
# Step definitions (reusable atoms)
# ---------------------------------------------------------------------------

def _step_register(state: str) -> Step:
    return Step(
        title="Register as a Voter",
        description=(
            f"New voters in {state} must enroll on the electoral roll before "
            f"the registration deadline."
        ),
        importance="critical",
        action=f"Visit {ECI_PORTAL} → 'New Voter Registration' and submit Form 6.",
    )


def _step_apply_id(state: str) -> Step:
    return Step(
        title="Apply for Voter ID (EPIC)",
        description=(
            "A Voter ID card (EPIC) is your primary photo ID for voting. "
            "Apply online or at your local ERO office."
        ),
        importance="critical",
        action=f"Go to {ECI_PORTAL} → 'Apply for EPIC' and complete the application.",
    )


def _step_verify(state: str) -> Step:
    return Step(
        title="Verify Your Enrollment",
        description=(
            f"Confirm your name appears on the {state} electoral roll "
            f"before polling day."
        ),
        importance="high",
        action=f"Search your name at {ECI_PORTAL} → 'Search in Electoral Roll'.",
    )


def _step_booth(state: str) -> Step:
    return Step(
        title="Find Your Polling Booth",
        description=(
            "Locate your assigned polling booth in advance so you know "
            "exactly where to go on election day."
        ),
        importance="high",
        action=f"Use the booth locator at {ECI_PORTAL} → 'Know Your Polling Station'.",
    )


def _step_carry_id() -> Step:
    return Step(
        title="Carry Valid Photo ID",
        description=(
            "Bring your Voter ID (EPIC) or any ECI-approved alternative ID "
            "(Aadhaar, Passport, PAN card, etc.) to the polling booth."
        ),
        importance="critical",
        action=(
            "Keep your Voter ID or an approved alternative ID ready on polling day. "
            "Check the full list of accepted IDs at voters.eci.gov.in."
        ),
    )


def _step_vote(state: str) -> Step:
    return Step(
        title="Cast Your Vote",
        description=(
            f"Visit your polling booth in {state} during polling hours, "
            f"present your ID, and cast your vote on the EVM."
        ),
        importance="critical",
        action=(
            "Arrive at your polling booth during official hours, collect your "
            "ballot slip, and press the button next to your chosen candidate on the EVM."
        ),
    )


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class ChecklistGenerator:

    @staticmethod
    def generate(profile: UserProfile) -> List[Step]:
        """
        Return a personalized checklist for an eligible voter.
        Branches on first_time_voter and has_voter_id.
        """
        state = profile.state or "your state"
        ftv = profile.first_time_voter
        hid = profile.has_voter_id

        if ftv and not hid:
            # New voter, no ID — full onboarding path
            return [
                _step_register(state),
                _step_apply_id(state),
                _step_verify(state),
                _step_booth(state),
                _step_carry_id(),
                _step_vote(state),
            ]

        if ftv and hid:
            # New voter who already has an ID
            return [
                _step_verify(state),
                _step_booth(state),
                _step_carry_id(),
                _step_vote(state),
            ]

        if not ftv and not hid:
            # Returning voter, lost or never got ID
            return [
                _step_apply_id(state),
                _step_verify(state),
                _step_booth(state),
                _step_carry_id(),
                _step_vote(state),
            ]

        # Returning voter with ID — shortest path
        return [
            _step_verify(state),
            _step_booth(state),
            _step_carry_id(),
            _step_vote(state),
        ]
