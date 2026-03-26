from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# -----------------------------
# Serve Frontend
# -----------------------------
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')


# -----------------------------
# Core AI Scheduling Logic
# -----------------------------
def schedule_event(data):
    speakers = data.get("speakers", [])
    venues = data.get("venues", [])
    budget = data.get("budget", 1000)
    interest = data.get("interest", "").lower()

    # Safety fallback
    if not speakers or not venues:
        return [], 0, ["No valid input provided"], []

    # Preferences
    preferences = {
        s["name"]: s.get("preference", 50) for s in speakers
    }

    # Agent 1: Experience Agent (sort by preference)
    speakers = sorted(speakers, key=lambda s: preferences[s["name"]], reverse=True)

    # Agent 2: Resource Agent (sort venues by capacity)
    venues = sorted(venues, key=lambda v: v["capacity"], reverse=True)

    used_slots = set()
    schedule = []
    explanation = []
    recommendations = []
    used_budget = 0

    # Weekly slots (tabular view)
    time_slots = ["Mon 10AM", "Tue 11AM", "Wed 12PM"]

    for sp in speakers:
        assigned = False

        for slot in time_slots:
            for venue in venues:

                # Conflict check
                if (slot, venue["name"]) in used_slots:
                    continue

                # Constraint checks
                if used_budget + sp["cost"] <= budget and venue["capacity"] >= sp["expected"]:

                    schedule.append({
                        "speaker": sp["name"],
                        "slot": slot,
                        "venue": venue["name"]
                    })

                    explanation.append(
                        f"[Planner] {sp['name']} scheduled at {slot} | "
                        f"[Resource] Budget OK ({used_budget + sp['cost']}/{budget}) | "
                        f"[Experience] Preference = {preferences[sp['name']]}"
                    )

                    # Attendee recommendation logic
                    if interest:
                        topic = sp.get("topic", "").lower()
                        if interest in topic or interest in sp["name"].lower():
                            recommendations.append(sp["name"])

                    used_slots.add((slot, venue["name"]))
                    used_budget += sp["cost"]
                    assigned = True
                    break

            if assigned:
                break

        if not assigned:
            explanation.append(
                f"[Conflict Resolver] {sp['name']} could NOT be scheduled "
                f"(budget/capacity/time conflict)"
            )

    return schedule, used_budget, explanation, recommendations


# -----------------------------
# API Endpoint
# -----------------------------
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}

    # Safe parsing
    try:
        data["budget"] = int(data.get("budget", 1000))
    except:
        data["budget"] = 1000

    schedule, budget_used, explanation, recommendations = schedule_event(data)

    return jsonify({
        "schedule": schedule,
        "budget": budget_used,
        "explanation": explanation,
        "recommendations": recommendations
    })


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)