"""
SessionStateManager — stores and retrieves UserProfile from the Flask session.
All profile data is serialized to plain dicts so Flask can store it in a
cookie-based or filesystem session without custom JSON encoders.
"""
from flask import session
from .models import UserProfile

SESSION_KEY = "voter_profile"


class SessionStateManager:
    @staticmethod
    def get_profile() -> UserProfile:
        """Return the current UserProfile from session, or a blank one."""
        raw = session.get(SESSION_KEY)
        if raw is None:
            return UserProfile()
        return UserProfile.from_dict(raw)

    @staticmethod
    def save_profile(profile: UserProfile) -> None:
        """Persist the UserProfile back into the session."""
        session[SESSION_KEY] = profile.to_dict()

    @staticmethod
    def clear() -> None:
        """Reset the session (e.g. on restart or new journey)."""
        session.pop(SESSION_KEY, None)
