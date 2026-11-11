"""
app.py
Main Flask application for the AI Nutrition Agent.
Exposes REST API endpoints consumed by the frontend.
"""

import os
import uuid
import json
import markdown as md
from flask import (
    Flask, request, jsonify, session,
    render_template, send_from_directory
)
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from nutrition_agent import agent
from user_profile   import (
    get_profile, update_profile, delete_profile,
    HEALTH_GOALS, DIETARY_PREFERENCES, ACTIVITY_LEVELS, CUISINES
)
from food_database  import lookup_food, format_nutrition_card, search_foods
from image_handler  import (
    extract_text_from_image, describe_image_context,
    allowed_file, encode_image_base64
)

# ── App setup ─────────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "nutrition-agent-dev-secret")
CORS(app)

UPLOAD_MAX_MB = 10
app.config["MAX_CONTENT_LENGTH"] = UPLOAD_MAX_MB * 1024 * 1024


def get_session_id() -> str:
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


def md_to_html(text: str) -> str:
    """Convert markdown response to HTML for frontend rendering."""
    return md.markdown(text, extensions=["tables", "fenced_code", "nl2br"])


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Profile endpoints ─────────────────────────────────────────────────────────

@app.route("/api/profile", methods=["GET"])
def get_user_profile():
    sid = get_session_id()
    profile = get_profile(sid)
    data = profile.to_dict()
    data["bmi"] = profile.bmi()
    data["bmi_category"] = profile.bmi_category()
    data["daily_calories"] = profile.daily_calories()
    return jsonify({"status": "ok", "profile": data})


@app.route("/api/profile", methods=["POST"])
def save_user_profile():
    sid  = get_session_id()
    data = request.get_json(force=True) or {}
    profile = update_profile(sid, data)
    return jsonify({
        "status": "ok",
        "message": "Profile updated successfully.",
        "bmi": profile.bmi(),
        "bmi_category": profile.bmi_category(),
        "daily_calories": profile.daily_calories(),
    })


@app.route("/api/profile/reset", methods=["POST"])
def reset_profile():
    sid = get_session_id()
    delete_profile(sid)
    session.pop("conversation", None)
    return jsonify({"status": "ok", "message": "Profile reset."})


@app.route("/api/metadata", methods=["GET"])
def get_metadata():
    """Return dropdown options for the profile form."""
    return jsonify({
        "health_goals":         HEALTH_GOALS,
        "dietary_preferences":  DIETARY_PREFERENCES,
        "activity_levels":      ACTIVITY_LEVELS,
        "cuisines":             CUISINES,
    })


# ── Meal plan endpoint ────────────────────────────────────────────────────────

@app.route("/api/meal-plan", methods=["POST"])
def meal_plan():
    sid     = get_session_id()
    profile = get_profile(sid)
    data    = request.get_json(force=True) or {}
    days    = int(data.get("days", 7))
    days    = max(1, min(days, 14))  # clamp 1-14

    result = agent.generate_meal_plan(profile, days=days)
    html   = md_to_html(result)
    return jsonify({"status": "ok", "meal_plan": result, "html": html})


# ── Food swap endpoint ────────────────────────────────────────────────────────

@app.route("/api/food-swap", methods=["POST"])
def food_swap():
    sid     = get_session_id()
    profile = get_profile(sid)
    data    = request.get_json(force=True) or {}
    foods   = data.get("foods", [])
    reason  = data.get("reason", "")

    if not foods:
        return jsonify({"status": "error", "message": "Please provide at least one food item."}), 400

    if isinstance(foods, str):
        foods = [f.strip() for f in foods.split(",")]

    result = agent.suggest_food_swaps(profile, foods, reason)
    html   = md_to_html(result)
    return jsonify({"status": "ok", "swaps": result, "html": html})


# ── Nutritional explanation endpoint ──────────────────────────────────────────

@app.route("/api/explain", methods=["POST"])
def explain_food():
    sid     = get_session_id()
    profile = get_profile(sid)
    data    = request.get_json(force=True) or {}
    food    = data.get("food", "").strip()

    if not food:
        return jsonify({"status": "error", "message": "Please provide a food name."}), 400

    result = agent.explain_food(profile, food)
    html   = md_to_html(result)
    return jsonify({"status": "ok", "explanation": result, "html": html})


# ── Chat endpoint ─────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    sid     = get_session_id()
    profile = get_profile(sid)
    data    = request.get_json(force=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"status": "error", "message": "Message cannot be empty."}), 400

    # Retrieve or init conversation history
    if "conversation" not in session:
        session["conversation"] = []

    history = session["conversation"]
    history.append({"role": "user", "content": message})

    response = agent.chat(profile, message, history)
    history.append({"role": "assistant", "content": response})

    # Keep last 20 turns in session
    session["conversation"] = history[-20:]
    session.modified = True

    html = md_to_html(response)
    return jsonify({"status": "ok", "response": response, "html": html})


@app.route("/api/chat/clear", methods=["POST"])
def clear_chat():
    session.pop("conversation", None)
    return jsonify({"status": "ok", "message": "Conversation cleared."})


# ── Image analysis endpoint ───────────────────────────────────────────────────

@app.route("/api/analyse-image", methods=["POST"])
def analyse_image():
    sid     = get_session_id()
    profile = get_profile(sid)

    if "image" not in request.files:
        return jsonify({"status": "error", "message": "No image file provided."}), 400

    file = request.files["image"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({
            "status": "error",
            "message": "Invalid file type. Please upload a PNG, JPG, JPEG, GIF, or WebP image."
        }), 400

    image_bytes = file.read()
    if len(image_bytes) > UPLOAD_MAX_MB * 1024 * 1024:
        return jsonify({"status": "error", "message": f"Image must be under {UPLOAD_MAX_MB}MB."}), 400

    image_context = describe_image_context(image_bytes)
    result        = agent.analyse_image_text(profile, image_context)
    html          = md_to_html(result)
    image_b64     = encode_image_base64(image_bytes)

    return jsonify({
        "status":        "ok",
        "analysis":      result,
        "html":          html,
        "extracted_text": image_context,
        "image_preview": f"data:image/jpeg;base64,{image_b64}",
    })


# ── Food lookup endpoint ──────────────────────────────────────────────────────

@app.route("/api/food-lookup", methods=["GET"])
def food_lookup():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"status": "error", "message": "Query parameter 'q' is required."}), 400

    food_data = lookup_food(query)
    card      = format_nutrition_card(food_data)
    results   = search_foods(query, limit=5)
    return jsonify({
        "status":      "ok",
        "food":        food_data,
        "card":        card,
        "suggestions": results,
    })


# ── Adaptive suggestions endpoint ─────────────────────────────────────────────

@app.route("/api/suggestions", methods=["GET"])
def adaptive_suggestions():
    sid     = get_session_id()
    profile = get_profile(sid)
    result  = agent.get_adaptive_suggestions(profile)
    html    = md_to_html(result)
    return jsonify({"status": "ok", "suggestions": result, "html": html})


# ── Feedback endpoint ─────────────────────────────────────────────────────────

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    sid     = get_session_id()
    profile = get_profile(sid)
    data    = request.get_json(force=True) or {}

    feedback_type = data.get("type", "meal")
    item          = data.get("item", "")
    rating        = int(data.get("rating", 3))
    note          = data.get("note", "")

    if not item:
        return jsonify({"status": "error", "message": "Item is required."}), 400
    if not (1 <= rating <= 5):
        return jsonify({"status": "error", "message": "Rating must be between 1 and 5."}), 400

    profile.add_feedback(feedback_type, item, rating, note)
    return jsonify({"status": "ok", "message": "Feedback recorded. Thank you!"})


# ── Health check ──────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health_check():
    from granite_client import granite
    return jsonify({
        "status":        "ok",
        "granite_ready": granite.is_ready,
        "mode":          "live" if granite.is_ready else "demo",
    })


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port  = int(os.getenv("PORT", 8080))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    print(f"\n🥗  AI Nutrition Agent running at http://localhost:{port}")
    print(f"   Mode: {'LIVE (IBM Granite connected)' if agent.client.is_ready else 'DEMO (configure .env for Granite)'}")
    app.run(host="0.0.0.0", port=port, debug=debug)
