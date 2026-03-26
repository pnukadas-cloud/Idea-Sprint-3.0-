from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@dataclass
class Speaker:
    name: str
    cost: int
    expected_attendees: int
    track: str
    available_slots: List[str]


@dataclass
class Venue:
    name: str
    capacity: int
    cost_per_slot: int
    available_slots: List[str]


@dataclass
class Assignment:
    speaker: str
    venue: str
    slot: str
    speaker_cost: int
    venue_cost: int
    attendee_score: int
    fit_score: float
    total_score: float


class SpeakerInput(BaseModel):
    name: str
    cost: int = Field(ge=0)
    expected_attendees: int = Field(ge=0)
    track: str
    available_slots: List[str]


class VenueInput(BaseModel):
    name: str
    capacity: int = Field(ge=0)
    cost_per_slot: int = Field(ge=0)
    available_slots: List[str]


class PreferenceInput(BaseModel):
    speaker_name: str
    score: int = Field(ge=0, le=100)


class PlanRequest(BaseModel):
    speakers: List[SpeakerInput]
    venues: List[VenueInput]
    preferences: List[PreferenceInput]
    budget_limit: int = Field(ge=0)
    time_slots: List[str]
    change_instruction: str = ""


class AttendeeExperienceOptimizer:
    def rank_speakers(
        self, speakers: List[Speaker], preferences: Dict[str, int]
    ) -> List[Speaker]:
        return sorted(
            speakers,
            key=lambda speaker: (
                preferences.get(normalize_key(speaker.name), 50),
                speaker.expected_attendees,
                -speaker.cost,
            ),
            reverse=True,
        )


class ResourceAllocator:
    def can_allocate(
        self,
        speaker: Speaker,
        venue: Venue,
        slot: str,
        budget_used: int,
        budget_limit: int,
    ) -> Tuple[bool, str]:
        if slot not in speaker.available_slots:
            return False, f"{speaker.name} unavailable at {slot}"
        if slot not in venue.available_slots:
            return False, f"{venue.name} unavailable at {slot}"

        incremental_cost = speaker.cost + venue.cost_per_slot
        if budget_used + incremental_cost > budget_limit:
            return False, "budget limit exceeded"
        if venue.capacity < speaker.expected_attendees:
            return False, f"{venue.name} capacity too small for {speaker.name}"
        return True, "allocation feasible"

    def score_assignment(
        self, speaker: Speaker, venue: Venue, preference_score: int
    ) -> Tuple[float, float]:
        capacity_gap = max(venue.capacity - speaker.expected_attendees, 0)
        fit_score = 100 - (capacity_gap / max(venue.capacity, 1)) * 100
        total_score = (
            preference_score * 0.55
            + fit_score * 0.30
            + speaker.expected_attendees * 0.20
            - venue.cost_per_slot * 0.05
            - speaker.cost * 0.02
        )
        return round(fit_score, 1), round(total_score, 1)


class SchedulingPlanner:
    def __init__(self) -> None:
        self.experience_optimizer = AttendeeExperienceOptimizer()
        self.resource_allocator = ResourceAllocator()

    def create_schedule(
        self,
        speakers: List[Speaker],
        venues: List[Venue],
        preferences: Dict[str, int],
        budget_limit: int,
        time_slots: List[str],
    ) -> Dict[str, object]:
        ranked_speakers = self.experience_optimizer.rank_speakers(speakers, preferences)
        speaker_lookup = {speaker.name: speaker for speaker in speakers}
        budget_used = 0
        assignments: List[Assignment] = []
        reasoning: List[str] = []
        unscheduled: List[Dict[str, str]] = []
        used_pairs = set()

        for speaker in ranked_speakers:
            best_candidate = None
            failure_reasons = []

            for slot in time_slots:
                for venue in venues:
                    pair = (slot, venue.name)
                    if pair in used_pairs:
                        continue

                    feasible, reason = self.resource_allocator.can_allocate(
                        speaker, venue, slot, budget_used, budget_limit
                    )
                    if not feasible:
                        failure_reasons.append(reason)
                        continue

                    fit_score, total_score = self.resource_allocator.score_assignment(
                        speaker, venue, preferences.get(normalize_key(speaker.name), 50)
                    )
                    candidate = Assignment(
                        speaker=speaker.name,
                        venue=venue.name,
                        slot=slot,
                        speaker_cost=speaker.cost,
                        venue_cost=venue.cost_per_slot,
                        attendee_score=preferences.get(normalize_key(speaker.name), 50),
                        fit_score=fit_score,
                        total_score=total_score,
                    )
                    if best_candidate is None or candidate.total_score > best_candidate.total_score:
                        best_candidate = candidate

            if best_candidate is None:
                unique_reasons = sorted(set(failure_reasons)) or ["no feasible placement"]
                unscheduled.append(
                    {
                        "speaker": speaker.name,
                        "reason": "; ".join(unique_reasons[:3]),
                    }
                )
                reasoning.append(
                    f"{speaker.name} left unscheduled. Blockers: {'; '.join(unique_reasons[:3])}."
                )
                continue

            assignments.append(best_candidate)
            used_pairs.add((best_candidate.slot, best_candidate.venue))
            budget_used += best_candidate.speaker_cost + best_candidate.venue_cost
            reasoning.append(
                f"{best_candidate.speaker} assigned to {best_candidate.venue} at "
                f"{best_candidate.slot}. Preference={best_candidate.attendee_score}, "
                f"fit={best_candidate.fit_score}, score={best_candidate.total_score}."
            )

        scheduled_attendees = sum(
            speaker_lookup[assignment.speaker].expected_attendees
            for assignment in assignments
        )

        return {
            "assignments": [asdict(item) for item in assignments],
            "unscheduled": unscheduled,
            "budget_limit": budget_limit,
            "budget_used": budget_used,
            "budget_remaining": budget_limit - budget_used,
            "budget_utilization": round((budget_used / budget_limit) * 100, 1)
            if budget_limit
            else 0,
            "scheduled_sessions": len(assignments),
            "unscheduled_sessions": len(unscheduled),
            "scheduled_attendees": scheduled_attendees,
            "agent_reasoning": reasoning,
        }


def clone_inputs(
    speakers: List[Speaker],
    venues: List[Venue],
    preferences: Dict[str, int],
) -> Tuple[List[Speaker], List[Venue], Dict[str, int]]:
    return (
        [
            Speaker(
                name=speaker.name,
                cost=speaker.cost,
                expected_attendees=speaker.expected_attendees,
                track=speaker.track,
                available_slots=list(speaker.available_slots),
            )
            for speaker in speakers
        ],
        [
            Venue(
                name=venue.name,
                capacity=venue.capacity,
                cost_per_slot=venue.cost_per_slot,
                available_slots=list(venue.available_slots),
            )
            for venue in venues
        ],
        dict(preferences),
    )


def normalize_key(value: str) -> str:
    return value.strip().lower()


def unique_slots(values: List[str]) -> List[str]:
    seen = set()
    ordered = []
    for value in values:
        slot = value.strip()
        if not slot:
            continue
        key = normalize_key(slot)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(slot)
    return ordered


def canonicalize_speakers(speakers: List[Speaker]) -> List[Speaker]:
    merged: Dict[str, Speaker] = {}
    for speaker in speakers:
        key = normalize_key(speaker.name)
        if key in merged:
            current = merged[key]
            current.name = speaker.name
            current.cost = speaker.cost
            current.expected_attendees = speaker.expected_attendees
            current.track = speaker.track
            current.available_slots = unique_slots(
                current.available_slots + speaker.available_slots
            )
            continue
        merged[key] = Speaker(
            name=speaker.name,
            cost=speaker.cost,
            expected_attendees=speaker.expected_attendees,
            track=speaker.track,
            available_slots=unique_slots(speaker.available_slots),
        )
    return list(merged.values())


def canonicalize_venues(venues: List[Venue]) -> List[Venue]:
    merged: Dict[str, Venue] = {}
    for venue in venues:
        key = normalize_key(venue.name)
        if key in merged:
            current = merged[key]
            current.name = venue.name
            current.capacity = venue.capacity
            current.cost_per_slot = venue.cost_per_slot
            current.available_slots = unique_slots(
                current.available_slots + venue.available_slots
            )
            continue
        merged[key] = Venue(
            name=venue.name,
            capacity=venue.capacity,
            cost_per_slot=venue.cost_per_slot,
            available_slots=unique_slots(venue.available_slots),
        )
    return list(merged.values())


def canonicalize_preferences(preferences: List[PreferenceInput]) -> Dict[str, int]:
    merged: Dict[str, int] = {}
    for item in preferences:
        merged[normalize_key(item.speaker_name)] = item.score
    return merged


def apply_change_instruction(
    speakers: List[Speaker],
    venues: List[Venue],
    preferences: Dict[str, int],
    budget_limit: int,
    instruction: str,
) -> Tuple[List[Speaker], List[Venue], Dict[str, int], int, str]:
    text = instruction.strip()
    if not text:
        return speakers, venues, preferences, budget_limit, "No last-minute change applied."

    parts = text.split()
    action = parts[0].lower()

    if action == "budget" and len(parts) >= 2:
        amount = int(" ".join(parts[1:]))
        return speakers, venues, preferences, amount, f"Budget updated to Rs.{amount}."

    if len(parts) < 3:
        raise ValueError(
            "Unsupported change instruction. Try 'cancel speaker Bob' or 'reduce venue Main Hall 30'."
        )

    entity = parts[1].lower()

    if action == "cancel" and entity == "speaker":
        speaker_name = " ".join(parts[2:])
        updated = [speaker for speaker in speakers if speaker.name.lower() != speaker_name.lower()]
        return updated, venues, preferences, budget_limit, f"Speaker {speaker_name} cancelled."

    if action == "remove" and entity == "slot":
        slot = " ".join(parts[2:])
        for speaker in speakers:
            speaker.available_slots = [item for item in speaker.available_slots if item != slot]
        for venue in venues:
            venue.available_slots = [item for item in venue.available_slots if item != slot]
        return speakers, venues, preferences, budget_limit, f"Removed slot {slot} across the event."

    if action == "reduce" and entity == "venue" and len(parts) >= 4:
        venue_name = " ".join(parts[2:-1])
        delta = int(parts[-1])
        for venue in venues:
            if venue.name.lower() == venue_name.lower():
                venue.capacity = max(0, venue.capacity - delta)
                return speakers, venues, preferences, budget_limit, (
                    f"Venue {venue.name} capacity reduced by {delta}."
                )
        raise ValueError(f"Venue '{venue_name}' not found.")

    if action == "increase" and entity == "preference" and len(parts) >= 4:
        speaker_name = " ".join(parts[2:-1])
        delta = int(parts[-1])
        for key in list(preferences):
            if normalize_key(key) == normalize_key(speaker_name):
                preferences[key] += delta
                return speakers, venues, preferences, budget_limit, (
                    f"Preference for {key} increased by {delta}."
                )
        raise ValueError(f"Speaker '{speaker_name}' not found in preferences.")

    raise ValueError(
        "Unsupported change instruction. Use 'cancel speaker NAME', 'reduce venue NAME 20', "
        "'increase preference NAME 10', 'remove slot 13:00', or 'budget 2600'."
    )


def sample_payload() -> Dict[str, object]:
    return {
        "budget_limit": 2200,
        "time_slots": ["09:00", "10:30", "13:00", "15:00"],
        "change_instruction": "cancel speaker Bob",
        "speakers": [
            {
                "name": "Alice",
                "cost": 500,
                "expected_attendees": 120,
                "track": "AI",
                "available_slots": ["09:00", "10:30"],
            },
            {
                "name": "Bob",
                "cost": 320,
                "expected_attendees": 70,
                "track": "Product",
                "available_slots": ["10:30", "13:00", "15:00"],
            },
            {
                "name": "Charlie",
                "cost": 450,
                "expected_attendees": 95,
                "track": "Engineering",
                "available_slots": ["09:00", "13:00"],
            },
            {
                "name": "Diana",
                "cost": 280,
                "expected_attendees": 55,
                "track": "Design",
                "available_slots": ["10:30", "15:00"],
            },
            {
                "name": "Ethan",
                "cost": 390,
                "expected_attendees": 85,
                "track": "Data",
                "available_slots": ["09:00", "15:00"],
            },
        ],
        "venues": [
            {
                "name": "Main Hall",
                "capacity": 150,
                "cost_per_slot": 180,
                "available_slots": ["09:00", "10:30", "13:00", "15:00"],
            },
            {
                "name": "Studio 1",
                "capacity": 90,
                "cost_per_slot": 100,
                "available_slots": ["09:00", "10:30", "13:00"],
            },
            {
                "name": "Studio 2",
                "capacity": 60,
                "cost_per_slot": 80,
                "available_slots": ["10:30", "13:00", "15:00"],
            },
        ],
        "preferences": [
            {"speaker_name": "Alice", "score": 98},
            {"speaker_name": "Bob", "score": 74},
            {"speaker_name": "Charlie", "score": 88},
            {"speaker_name": "Diana", "score": 80},
            {"speaker_name": "Ethan", "score": 91},
        ],
    }


def execute_plan(request: PlanRequest) -> Dict[str, object]:
    if not request.time_slots:
        raise ValueError("At least one time slot is required.")

    speakers = canonicalize_speakers(
        [Speaker(**item.model_dump()) for item in request.speakers]
    )
    venues = canonicalize_venues(
        [Venue(**item.model_dump()) for item in request.venues]
    )
    preferences = canonicalize_preferences(request.preferences)

    planner = SchedulingPlanner()
    baseline = planner.create_schedule(
        speakers=speakers,
        venues=venues,
        preferences=preferences,
        budget_limit=request.budget_limit,
        time_slots=request.time_slots,
    )

    replanning_inputs = clone_inputs(speakers, venues, preferences)
    updated_speakers, updated_venues, updated_preferences, updated_budget, change_summary = (
        apply_change_instruction(
            speakers=replanning_inputs[0],
            venues=replanning_inputs[1],
            preferences=replanning_inputs[2],
            budget_limit=request.budget_limit,
            instruction=request.change_instruction,
        )
    )

    replanned = planner.create_schedule(
        speakers=updated_speakers,
        venues=updated_venues,
        preferences=updated_preferences,
        budget_limit=updated_budget,
        time_slots=request.time_slots,
    )

    impact = {
        "change_applied": change_summary,
        "baseline_sessions": baseline["scheduled_sessions"],
        "replanned_sessions": replanned["scheduled_sessions"],
        "baseline_budget_used": baseline["budget_used"],
        "replanned_budget_used": replanned["budget_used"],
        "baseline_attendees": baseline["scheduled_attendees"],
        "replanned_attendees": replanned["scheduled_attendees"],
        "delta_sessions": replanned["scheduled_sessions"] - baseline["scheduled_sessions"],
        "delta_budget": replanned["budget_used"] - baseline["budget_used"],
        "delta_attendees": replanned["scheduled_attendees"] - baseline["scheduled_attendees"],
    }

    return {
        "baseline": baseline,
        "replanned": replanned,
        "impact": impact,
    }


app = FastAPI(title="Northstar Events")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(BASE_DIR / "index.html")


@app.get("/api/sample")
async def get_sample() -> Dict[str, object]:
    return sample_payload()


@app.post("/api/plan")
async def plan_event(request: PlanRequest) -> Dict[str, object]:
    try:
        return execute_plan(request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
