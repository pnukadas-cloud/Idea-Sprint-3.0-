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

    used = set()
    schedule = []
    explanation = []
    recommendations = []
    used_budget = 0

    time_slots = ["Mon 10AM", "Tue 11AM", "Wed 12PM"]

    for sp in speakers:
        assigned = False

        for t in time_slots:
            for v in venues:

                if (t, v["name"]) in used:
                    continue

                if used_budget + sp["cost"] <= budget and v["capacity"] >= sp["expected"]:
                    schedule.append({
                        "speaker": sp["name"],
                        "slot": t,
                        "venue": v["name"]
                    })

                    explanation.append(
                        f"[Planner] {sp['name']} → {t} | "
                        f"[Resource] Budget OK | "
                        f"[Experience] Preference {preferences[sp['name']]}"
                    )

                    # Attendee recommendations
                    if interest and (interest in sp["name"].lower() or interest in sp.get("topic","").lower()):
                        recommendations.append(sp["name"])

                    used.add((t, v["name"]))
                    used_budget += sp["cost"]
                    assigned = True
                    break

            if assigned:
                break

        if not assigned:
            explanation.append(f"{sp['name']} could NOT be scheduled")

    return schedule, used_budget, explanation, recommendations


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()

    schedule, budget_used, explanation, recommendations = schedule_event(data)

    return jsonify({
        "schedule": schedule,
        "budget": budget_used,
        "explanation": explanation,
        "recommendations": recommendations
    })


if __name__ == "__main__":
    app.run(debug=True)