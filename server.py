from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# Serve HTML safely
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

# API endpoint
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}

    # Safe budget parsing
    budget_value = data.get("budget", 0)

    try:
        budget = int(budget_value)
    except (ValueError, TypeError):
        budget = 0

    # Sample logic
    schedule = [
        "🎤 Speaker A - Opening Talk",
        "📊 Speaker B - Tech Trends",
        "🤝 Networking Session"
    ]

    budget_used = max(budget - 200, 0)

    explanation = [
        "Selected speakers based on budget",
        "Reserved funds for logistics",
        "Balanced schedule for engagement"
    ]

    return jsonify({
        "schedule": schedule,
        "budget": budget_used,
        "explanation": explanation
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)