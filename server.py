from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# Serve your HTML
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

# API endpoint (this replaces your Gradio logic)
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    budget = data.get("budget")

    # Your logic here (simple example)
    schedule = ["Speaker A", "Speaker B"]
    budget_used = budget - 200
    decisions = ["Picked affordable speakers"]

    return jsonify({
        "schedule": schedule,
        "budget_used": budget_used,
        "decisions": decisions
    })

if __name__ == "__main__":
    app.run(debug=True)