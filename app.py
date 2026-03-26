import gradio as gr

# -----------------------------
# Agent Functions
# -----------------------------

def experience_agent(speakers, preferences):
    return sorted(speakers, key=lambda s: preferences.get(s["name"], 0), reverse=True)

def resource_agent(speaker, venue, current_budget, budget_limit):
    if current_budget + speaker["cost"] > budget_limit:
        return False
    if venue["capacity"] < speaker["expected"]:
        return False
    return True

def scheduling_agent(speakers, venues, budget_limit, preferences):
    schedule = []
    used = set()
    budget = 0
    explanation = []

    speakers = experience_agent(speakers, preferences)
    venues = sorted(venues, key=lambda v: v["capacity"], reverse=True)

    time_slots = ["10AM", "11AM", "12PM"]

    for sp in speakers:
        assigned = False
        for t in time_slots:
            for v in venues:
                key = (t, v["name"])
                if key in used:
                    continue

                if resource_agent(sp, v, budget, budget_limit):
                    schedule.append(f"{sp['name']} → {v['name']} at {t}")
                    used.add(key)
                    budget += sp["cost"]

                    explanation.append(
                        f"{sp['name']} assigned to {v['name']} at {t} "
                        f"(pref={preferences[sp['name']]}, capacity={v['capacity']})"
                    )
                    assigned = True
                    break
            if assigned:
                break

        if not assigned:
            explanation.append(f"{sp['name']} could NOT be scheduled (constraints issue)")

    return "\n".join(schedule), budget, "\n".join(explanation)


# -----------------------------
# Main Bot Function
# -----------------------------

def run_planner(budget):
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

    schedule, budget_used, explanation = scheduling_agent(
        speakers, venues, budget, preferences
    )

    return (
        f"📅 SCHEDULE:\n{schedule}\n\n"
        f"💰 Budget Used: {budget_used}\n\n"
        f"🤖 AI Decisions:\n{explanation}"
    )


# -----------------------------
# Gradio App
# -----------------------------

app = gr.Interface(
    fn=run_planner,
    inputs=gr.Slider(500, 1500, step=100, label="Budget"),
    outputs="text",
    title="🤖 AI Event Planning Agent",
    description="Adjust budget and see how AI re-plans the event dynamically."
)

if __name__ == "__main__":
    app.launch(share=True)