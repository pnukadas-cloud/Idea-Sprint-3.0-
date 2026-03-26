from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')


def schedule_event(data):
    speakers = data.get("speakers", [])
    venues = data.get("venues", [])
    budget = data.get("budget", 1000)

    preferences = {s["name"]: s.get("preference", 50) for s in speakers}

    # Agent 1: Experience Agent
    speakers = sorted(speakers, key=lambda s: preferences[s["name"]], reverse=True)

    # Agent 2: Resource Agent
    venues = sorted(venues, key=lambda v: v["capacity"], reverse=True)

    used = set()
    schedule = []
    explanation = []
    used_budget = 0

    time_slots = ["10AM", "11AM", "12PM"]

    for sp in speakers:
        assigned = False

        for t in time_slots:
            for v in venues:

                if (t, v["name"]) in used:
                    continue

                if used_budget + sp["cost"] <= budget and v["capacity"] >= sp["expected"]:
                    schedule.append(f"{sp['name']} → {v['name']} at {t}")

                    explanation.append(
                        f"[Planner Agent] Assigned {sp['name']} at {t}\n"
                        f"[Resource Agent] Budget OK, Capacity OK\n"
                        f"[Experience Agent] High preference ({preferences[sp['name']]})"
                    )

                    used.add((t, v["name"]))
                    used_budget += sp["cost"]
                    assigned = True
                    break

            if assigned:
                break

        if not assigned:
            explanation.append(
                f"{sp['name']} could NOT be scheduled (conflict/budget issue)"
            )

    return schedule, used_budget, explanation


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()

    schedule, budget_used, explanation = schedule_event(data)

    return jsonify({
        "schedule": schedule,
        "budget": budget_used,
        "explanation": explanation
    })


if __name__ == "__main__":
    app.run(debug=True)