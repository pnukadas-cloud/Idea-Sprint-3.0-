from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')


def schedule_event(data):
    speakers = data.get("speakers", [])
    venues = data.get("venues", [])
    budget = data.get("budget", 1000)
    interest = data.get("interest", "").lower()

    preferences = {s["name"]: s.get("preference", 50) for s in speakers}

    speakers = sorted(speakers, key=lambda s: preferences[s["name"]], reverse=True)
    venues = sorted(venues, key=lambda v: v["capacity"], reverse=True)

    used_slots = set()
    schedule = []
    explanation = []
    recommendations = []
    used_budget = 0

    time_slots = ["Mon 10AM", "Tue 11AM", "Wed 12PM", "Thu 1PM", "Fri 2PM"]

    for sp in speakers:
        assigned = False

        for slot in time_slots:
            for venue in venues:

                if (slot, venue["name"]) in used_slots:
                    continue

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
                f"[Conflict Resolver] {sp['name']} not scheduled (no slot/budget/capacity)"
            )

    return schedule, used_budget, explanation, recommendations


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}

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


if __name__ == "__main__":
    app.run(debug=True)