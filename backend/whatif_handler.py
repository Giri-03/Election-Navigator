"""
What-If Handler — returns a list of recovery steps (≥2) for each
of the four WhatIfScenario values.

All steps reference ECI processes as required by Requirements 5.1–5.4.
"""
from __future__ import annotations

from typing import List, Optional


_RECOVERY_STEPS: dict = {
    "missed_deadline": [
        "Check the ECI website (voters.eci.gov.in) for any extended or special "
        "registration windows — deadlines are sometimes revised before polling day.",
        "Contact your local Electoral Registration Officer (ERO) directly; they can "
        "advise on late-enrollment options under the Representation of the People Act.",
        "If a by-election or supplementary roll revision is announced, submit Form 6 "
        "immediately at voters.eci.gov.in to be included in the updated roll.",
        "Download the Voter Helpline App or call the ECI helpline (1950) to get "
        "state-specific guidance on your options.",
    ],
    "lost_id": [
        "You can still vote using any of the ECI-approved alternative photo IDs: "
        "Aadhaar card, Passport, PAN card, Driving Licence, MNREGA Job Card, "
        "Bank/Post Office Passbook with photo, or a Smart Card issued by RGI.",
        "Apply for a duplicate Voter ID (EPIC) online at voters.eci.gov.in → "
        "'Apply for EPIC' → select 'Replacement of EPIC' and submit the form.",
        "Visit your local ERO office with a copy of your FIR (if the ID was stolen) "
        "or a self-declaration of loss to expedite the duplicate ID process.",
        "Call the ECI Voter Helpline (1950) for guidance on same-day alternatives "
        "if polling day is imminent.",
    ],
    "missing_from_voter_list": [
        "Search your name on the electoral roll at voters.eci.gov.in → "
        "'Search in Electoral Roll' using your name, EPIC number, or mobile number.",
        "If your name is missing, submit Form 6 (new registration) at voters.eci.gov.in "
        "or at your local ERO office before the next roll revision deadline.",
        "File a complaint via the National Voter Service Portal (NVSP) or the "
        "Voter Helpline App if you believe your name was incorrectly deleted.",
        "Contact your local Booth Level Officer (BLO) — they can verify and correct "
        "enrollment errors at the booth level before the final roll is published.",
    ],
    "relocated": [
        "Submit Form 8A (transposition of entry) at voters.eci.gov.in to transfer "
        "your voter registration to your new constituency without re-registering.",
        "If you have moved to a different state, submit Form 6 for fresh registration "
        "in the new state and Form 7 to delete your old entry simultaneously.",
        "Contact the ERO of your new constituency to confirm the transfer timeline "
        "and ensure you are enrolled before the next polling date.",
        "Use the Voter Helpline App or call 1950 to track the status of your "
        "transfer request and confirm your new polling booth assignment.",
    ],
}


class WhatIfHandler:

    @staticmethod
    def get_recovery_steps(scenario: str) -> List[str]:
        """
        Return a list of recovery steps for the given scenario.
        Returns an empty list for unknown scenarios (caller should handle).
        """
        return list(_RECOVERY_STEPS.get(scenario, []))

    @staticmethod
    def get_message(scenario: str) -> str:
        """Return a short summary message for the scenario."""
        messages = {
            "missed_deadline": "You may have missed the registration deadline — but there are still options.",
            "lost_id": "A lost Voter ID doesn't have to stop you from voting.",
            "missing_from_voter_list": "Your name may be missing from the voter list — here's how to fix it.",
            "relocated": "Moving to a new area means updating your voter registration.",
        }
        return messages.get(scenario, "Here are your recovery options.")
