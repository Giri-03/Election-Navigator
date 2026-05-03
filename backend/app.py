from flask import Flask, request, jsonify, session
import os

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "../frontend/templates"),
    static_folder=os.path.join(BASE_DIR, "../frontend/static"),
)
)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    from flask import render_template
    from .session_manager import SessionStateManager
    SessionStateManager.clear()  # fresh start on every page load
    return render_template("index.html")


@app.route("/reset", methods=["POST"])
def reset():
    """Clear session state to start a new journey."""
    from .session_manager import SessionStateManager
    SessionStateManager.clear()
    return jsonify({"status": "reset"})


@app.route("/chat_flow", methods=["POST"])
def chat_flow():
    """
    Primary endpoint — advances session state, returns full NavigatorResponse.
    Body: { "message": "string", "steps": [...] }
    """
    from .orchestrator import Orchestrator, InvalidResponseError
    data = request.get_json(force=True) or {}
    message = data.get("message", "")
    session_steps = data.get("steps", [])

    try:
        result = Orchestrator.process(message, session_steps)
        return jsonify(result)
    except InvalidResponseError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


@app.route("/check_eligibility", methods=["POST"])
def check_eligibility():
    """
    Standalone eligibility check.
    Body: { "age": int, "citizenship": str, "state": str }
    """
    from .models import UserProfile
    from .eligibility_checker import EligibilityChecker
    data = request.get_json(force=True) or {}

    try:
        age = int(data.get("age", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "age must be an integer"}), 400

    profile = UserProfile(
        age=age,
        citizenship=data.get("citizenship", "").lower().strip(),
        state=data.get("state", ""),
        first_time_voter=False,
        has_voter_id=False,
    )
    result = EligibilityChecker.check(profile)
    return jsonify(result.to_dict())


@app.route("/get_timeline", methods=["GET"])
def get_timeline():
    """
    Returns the 4-milestone timeline for the current session's state.
    Falls back to generic ECI dates if no state in session.
    """
    from .session_manager import SessionStateManager
    from .timeline_generator import TimelineGenerator
    profile = SessionStateManager.get_profile()
    state = profile.state or ""
    milestones = TimelineGenerator.generate(state)
    return jsonify({"timeline": [m.to_dict() for m in milestones]})


@app.route("/generate_steps", methods=["POST"])
def generate_steps():
    """
    Returns the personalized checklist for a given profile.
    Body: { "first_time_voter": bool, "has_voter_id": bool, "state": str }
    """
    from .models import UserProfile
    from .checklist_generator import ChecklistGenerator
    data = request.get_json(force=True) or {}

    profile = UserProfile(
        age=18,  # assumed eligible for this standalone endpoint
        citizenship="indian",
        state=data.get("state", ""),
        first_time_voter=bool(data.get("first_time_voter", False)),
        has_voter_id=bool(data.get("has_voter_id", False)),
    )
    steps = ChecklistGenerator.generate(profile)
    return jsonify({"steps": [s.to_dict() for s in steps]})


if __name__ == "__main__":
    app.run(debug=True)
