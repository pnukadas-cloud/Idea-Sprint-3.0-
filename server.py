from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# -----------------------------
# Serve HTML
# -----------------------------
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')


# -----------------------------
# AI Scheduling Logic
# -----------------------------
def schedule_event(budget):

    speakers = [
        {"name": "Alice", "cost": 500, "expected": 90},
        {"name": "Bob", "cost": 300, "expected": 40},
        {"name": "Charlie", "cost": 400, "expected": 60},
    ]

    venues = [
        {"name": "Hall A", "capacity": 100},
        {"name": "Hall B", "capacity": 50},
    ]

    preferences = {
        "Alice": 95,
        "Bob": 70,
        "Charlie": 85
    }

    # Experience Agent → sort by popularity
    speakers = sorted(speakers, key=lambda s: preferences[s["name"]], reverse=True)

    # Resource Agent → sort venues
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

                # Constraints check
                if used_budget + sp["cost"] <= budget and v["capacity"] >= sp["expected"]:
                    schedule.append(f"{sp['name']} → {v['name']} at {t}")

                    explanation.append(
                        f"{sp['name']} assigned to {v['name']} at {t} "
                        f"(Preference={preferences[sp['name']]}, Capacity={v['capacity']})"
                    )

                    used.add((t, v["name"]))
                    used_budget += sp["cost"]
                    assigned = True
                    break

            if assigned:
                break

        if not assigned:
            explanation.append(
                f"{sp['name']} could NOT be scheduled due to constraints"
            )

    return schedule, used_budget, explanation


# -----------------------------
# API endpoint
# -----------------------------
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}

    try:
        budget = int(data.get("budget", 1000))
    except:
        budget = 1000

    schedule, budget_used, explanation = schedule_event(budget)

    return jsonify({
        "schedule": schedule,
        "budget": budget_used,
        "explanation": explanation
    })


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)