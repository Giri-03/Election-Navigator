"""
Timeline Generator — returns exactly 4 TimelineMilestone objects:
  registration → verification → polling → result

Dates are mock/approximate and clearly labeled "(approx. — verify with local CEO)".
State-specific data is used when available; falls back to generic ECI-level dates.
All data is clearly marked as simulated (Requirement 4.2, 4.3, 8.3, 8.4).
"""
from __future__ import annotations

from typing import List

from .models import TimelineMilestone

APPROX_LABEL = "(approx. — verify with local CEO)"

# ---------------------------------------------------------------------------
# State-localized mock timeline data
# Keys are lowercase state names for case-insensitive lookup.
# Each entry has date strings for the four milestones.
# ---------------------------------------------------------------------------

_STATE_TIMELINES: dict = {
    "maharashtra": {
        "registration": ("Sep 1 – Oct 15", "Register or update your enrollment on the Maharashtra electoral roll."),
        "verification": ("Oct 16 – Nov 1",  "Verify your name and polling booth assignment via the ECI portal."),
        "polling":      ("Nov 20",           "Cast your vote at your assigned polling booth in Maharashtra."),
        "result":       ("Nov 23",           "Election results declared for Maharashtra constituencies."),
    },
    "delhi": {
        "registration": ("Aug 15 – Sep 30", "Register or update your enrollment on the Delhi electoral roll."),
        "verification": ("Oct 1 – Oct 20",  "Verify your name and polling booth assignment via the ECI portal."),
        "polling":      ("Nov 5",            "Cast your vote at your assigned polling booth in Delhi."),
        "result":       ("Nov 8",            "Election results declared for Delhi constituencies."),
    },
    "karnataka": {
        "registration": ("Jan 1 – Feb 15",  "Register or update your enrollment on the Karnataka electoral roll."),
        "verification": ("Feb 16 – Mar 1",  "Verify your name and polling booth assignment via the ECI portal."),
        "polling":      ("Apr 10",           "Cast your vote at your assigned polling booth in Karnataka."),
        "result":       ("Apr 13",           "Election results declared for Karnataka constituencies."),
    },
    "tamil nadu": {
        "registration": ("Jan 15 – Mar 1",  "Register or update your enrollment on the Tamil Nadu electoral roll."),
        "verification": ("Mar 2 – Mar 20",  "Verify your name and polling booth assignment via the ECI portal."),
        "polling":      ("Apr 19",           "Cast your vote at your assigned polling booth in Tamil Nadu."),
        "result":       ("Jun 4",            "Election results declared for Tamil Nadu constituencies."),
    },
    "uttar pradesh": {
        "registration": ("Oct 1 – Nov 15",  "Register or update your enrollment on the Uttar Pradesh electoral roll."),
        "verification": ("Nov 16 – Dec 1",  "Verify your name and polling booth assignment via the ECI portal."),
        "polling":      ("Feb 10 – Mar 7",  "Cast your vote across multiple phases in Uttar Pradesh."),
        "result":       ("Mar 10",           "Election results declared for Uttar Pradesh constituencies."),
    },
    "west bengal": {
        "registration": ("Nov 1 – Dec 15",  "Register or update your enrollment on the West Bengal electoral roll."),
        "verification": ("Dec 16 – Jan 5",  "Verify your name and polling booth assignment via the ECI portal."),
        "polling":      ("Mar 27 – Apr 29", "Cast your vote across multiple phases in West Bengal."),
        "result":       ("May 2",            "Election results declared for West Bengal constituencies."),
    },
    "gujarat": {
        "registration": ("Aug 1 – Sep 15",  "Register or update your enrollment on the Gujarat electoral roll."),
        "verification": ("Sep 16 – Oct 1",  "Verify your name and polling booth assignment via the ECI portal."),
        "polling":      ("Dec 1 – Dec 5",   "Cast your vote across two phases in Gujarat."),
        "result":       ("Dec 8",            "Election results declared for Gujarat constituencies."),
    },
    "rajasthan": {
        "registration": ("Aug 15 – Oct 1",  "Register or update your enrollment on the Rajasthan electoral roll."),
        "verification": ("Oct 2 – Oct 20",  "Verify your name and polling booth assignment via the ECI portal."),
        "polling":      ("Nov 25",           "Cast your vote at your assigned polling booth in Rajasthan."),
        "result":       ("Dec 3",            "Election results declared for Rajasthan constituencies."),
    },
    "kerala": {
        "registration": ("Jan 1 – Feb 28",  "Register or update your enrollment on the Kerala electoral roll."),
        "verification": ("Mar 1 – Mar 20",  "Verify your name and polling booth assignment via the ECI portal."),
        "polling":      ("Apr 26",           "Cast your vote at your assigned polling booth in Kerala."),
        "result":       ("Jun 4",            "Election results declared for Kerala constituencies."),
    },
    "punjab": {
        "registration": ("Oct 1 – Nov 30",  "Register or update your enrollment on the Punjab electoral roll."),
        "verification": ("Dec 1 – Dec 20",  "Verify your name and polling booth assignment via the ECI portal."),
        "polling":      ("Feb 20",           "Cast your vote at your assigned polling booth in Punjab."),
        "result":       ("Mar 10",           "Election results declared for Punjab constituencies."),
    },
}

# Generic ECI-level fallback (used when state not in the dict above)
_GENERIC_TIMELINE = {
    "registration": ("Varies by state",    "Register or update your enrollment before the state-specific deadline."),
    "verification": ("After registration", "Verify your name on the electoral roll at voters.eci.gov.in."),
    "polling":      ("As announced by ECI","Cast your vote at your assigned polling booth on polling day."),
    "result":       ("After polling day",  "Election results are declared by the Election Commission of India."),
}

MILESTONE_ORDER = ["registration", "verification", "polling", "result"]


class TimelineGenerator:

    @staticmethod
    def generate(state: str) -> List[TimelineMilestone]:
        """
        Return exactly 4 TimelineMilestone objects for the given state.
        Falls back to generic ECI dates if state not in local data.
        All date_range values are suffixed with the approx label.
        """
        key = (state or "").lower().strip()
        data = _STATE_TIMELINES.get(key, _GENERIC_TIMELINE)

        milestones: List[TimelineMilestone] = []
        for label in MILESTONE_ORDER:
            date_str, description = data[label]
            milestones.append(TimelineMilestone(
                label=label,
                date_range=f"{date_str} {APPROX_LABEL}",
                description=description,
            ))

        return milestones
