# AI Agent for Dynamic Event Planning

This project now uses a standard web architecture:

- Python backend with FastAPI
- custom frontend with HTML, CSS, and JavaScript
- agent-style planning logic for scheduling, resource allocation, and attendee experience optimization

## What It Does

- creates a feasible event schedule from speakers, venues, preferences, budget, and time slots
- detects and handles capacity, availability, and budget conflicts
- re-optimizes the schedule when constraints change
- shows why the agents made each scheduling decision

## Project Structure

- [app.py](C:\Users\Punith Venkat Sai\OneDrive\Desktop\Idea-Sprint-3.0-\app.py): FastAPI server and planning engine
- [static/index.html](C:\Users\Punith Venkat Sai\OneDrive\Desktop\Idea-Sprint-3.0-\static\index.html): main dashboard UI
- [static/styles.css](C:\Users\Punith Venkat Sai\OneDrive\Desktop\Idea-Sprint-3.0-\static\styles.css): visual design and responsive layout
- [static/app.js](C:\Users\Punith Venkat Sai\OneDrive\Desktop\Idea-Sprint-3.0-\static\app.js): client-side interactions, API calls, and rendering
- [run_app.bat](C:\Users\Punith Venkat Sai\OneDrive\Desktop\Idea-Sprint-3.0-\run_app.bat): local launcher

## Run

If you already have Python on your machine:

```bash
pip install -r requirements.txt
python app.py
```

For this workspace, a local Python runtime is already prepared, so the fastest option is:

```bash
run_app.bat
```

Then open:

```text
http://127.0.0.1:8000
```

## Supported Change Simulations

- `cancel speaker Bob`
- `reduce venue Main Hall 30`
- `remove slot 13:00`
- `increase preference Alice 10`
- `budget 2600`
