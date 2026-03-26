const elements = {
  budgetLimit: document.getElementById("budget-limit"),
  timeSlots: document.getElementById("time-slots"),
  changeInstruction: document.getElementById("change-instruction"),
  runPlanner: document.getElementById("run-planner"),
  loadSample: document.getElementById("load-sample"),
  addSpeaker: document.getElementById("add-speaker"),
  addVenue: document.getElementById("add-venue"),
  addPreference: document.getElementById("add-preference"),
  speakersBody: document.getElementById("speakers-body"),
  venuesBody: document.getElementById("venues-body"),
  preferencesBody: document.getElementById("preferences-body"),
  baselineTable: document.getElementById("baseline-table"),
  replannedTable: document.getElementById("replanned-table"),
  baselineReasoning: document.getElementById("baseline-reasoning"),
  replannedReasoning: document.getElementById("replanned-reasoning"),
  baselineSummary: document.getElementById("baseline-summary"),
  replannedSummary: document.getElementById("replanned-summary"),
  baselineUnscheduled: document.getElementById("baseline-unscheduled"),
  replannedUnscheduled: document.getElementById("replanned-unscheduled"),
  impactGrid: document.getElementById("impact-grid"),
  rawOutput: document.getElementById("raw-output"),
  changeSummary: document.getElementById("change-summary"),
  metricSessions: document.getElementById("metric-sessions"),
  metricBudget: document.getElementById("metric-budget"),
  metricAttendees: document.getElementById("metric-attendees"),
  impactCardTemplate: document.getElementById("impact-card-template"),
};

const STORAGE_KEY = "event-planner-draft-v2";
const API_BASE = window.location.port === "8000" ? "" : "http://127.0.0.1:8000";

const defaultRows = {
  speaker: {
    name: "",
    cost: "",
    expected_attendees: "",
    track: "",
    available_slots: "",
  },
  venue: {
    name: "",
    capacity: "",
    cost_per_slot: "",
    available_slots: "",
  },
  preference: {
    speaker_name: "",
    score: "",
  },
};

function formatMoney(value) {
  return `Rs.${Number(value || 0).toLocaleString()}`;
}

function formatDelta(value) {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value}`;
}

function parseSlotList(text) {
  return String(text || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function createCellInput(value, placeholder = "", type = "text") {
  const input = document.createElement("input");
  input.type = type;
  input.value = value ?? "";
  input.placeholder = placeholder;
  input.autocomplete = "off";
  input.spellcheck = false;
  return input;
}

function createDeleteButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "table-delete";
  button.textContent = "Remove";
  return button;
}

function makeSpeakerRow(data = defaultRows.speaker) {
  const row = document.createElement("tr");
  row.innerHTML = `
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td class="action-cell"></td>
  `;

  row.children[0].appendChild(createCellInput(data.name, "Alice"));
  row.children[1].appendChild(createCellInput(data.cost, "500", "number"));
  row.children[2].appendChild(createCellInput(data.expected_attendees, "120", "number"));
  row.children[3].appendChild(createCellInput(data.track, "AI"));
  row.children[4].appendChild(createCellInput(data.available_slots, "09:00,10:30"));
  row.children[5].appendChild(createDeleteButton());
  return row;
}

function makeVenueRow(data = defaultRows.venue) {
  const row = document.createElement("tr");
  row.innerHTML = `
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td class="action-cell"></td>
  `;

  row.children[0].appendChild(createCellInput(data.name, "Main Hall"));
  row.children[1].appendChild(createCellInput(data.capacity, "150", "number"));
  row.children[2].appendChild(createCellInput(data.cost_per_slot, "180", "number"));
  row.children[3].appendChild(createCellInput(data.available_slots, "09:00,10:30,13:00"));
  row.children[4].appendChild(createDeleteButton());
  return row;
}

function makePreferenceRow(data = defaultRows.preference) {
  const row = document.createElement("tr");
  row.innerHTML = `
    <td></td>
    <td></td>
    <td class="action-cell"></td>
  `;

  row.children[0].appendChild(createCellInput(data.speaker_name, "Alice"));
  row.children[1].appendChild(createCellInput(data.score, "98", "number"));
  row.children[2].appendChild(createDeleteButton());
  return row;
}

function rowValue(row, index) {
  const input = row.children[index].querySelector("input");
  return input ? input.value.trim() : "";
}

function collectSpeakers() {
  return [...elements.speakersBody.children]
    .map((row) => ({
      name: rowValue(row, 0),
      cost: Number(rowValue(row, 1) || 0),
      expected_attendees: Number(rowValue(row, 2) || 0),
      track: rowValue(row, 3),
      available_slots: parseSlotList(rowValue(row, 4)),
    }))
    .filter((item) => item.name);
}

function collectVenues() {
  return [...elements.venuesBody.children]
    .map((row) => ({
      name: rowValue(row, 0),
      capacity: Number(rowValue(row, 1) || 0),
      cost_per_slot: Number(rowValue(row, 2) || 0),
      available_slots: parseSlotList(rowValue(row, 3)),
    }))
    .filter((item) => item.name);
}

function collectPreferences() {
  return [...elements.preferencesBody.children]
    .map((row) => ({
      speaker_name: rowValue(row, 0),
      score: Number(rowValue(row, 1) || 0),
    }))
    .filter((item) => item.speaker_name);
}

function collectPayload() {
  return {
    budget_limit: Number(elements.budgetLimit.value || 0),
    time_slots: parseSlotList(elements.timeSlots.value),
    change_instruction: elements.changeInstruction.value.trim(),
    speakers: collectSpeakers(),
    venues: collectVenues(),
    preferences: collectPreferences(),
  };
}

function snapshotDraft() {
  return {
    budget_limit: elements.budgetLimit.value,
    time_slots: elements.timeSlots.value,
    change_instruction: elements.changeInstruction.value,
    speakers: collectSpeakers(),
    venues: collectVenues(),
    preferences: collectPreferences(),
  };
}

function persistDraft() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshotDraft()));
}

function clearTable(body) {
  body.innerHTML = "";
}

function populateEditorTable(body, rows, factory) {
  clearTable(body);
  rows.forEach((row) => body.appendChild(factory(row)));
  if (!rows.length) {
    body.appendChild(factory());
  }
}

function populateInputs(payload) {
  elements.budgetLimit.value = payload.budget_limit;
  elements.timeSlots.value = payload.time_slots.join(", ");
  elements.changeInstruction.value = payload.change_instruction || "";
  populateEditorTable(
    elements.speakersBody,
    payload.speakers.map((item) => ({
      ...item,
      available_slots: item.available_slots.join(", "),
    })),
    makeSpeakerRow
  );
  populateEditorTable(
    elements.venuesBody,
    payload.venues.map((item) => ({
      ...item,
      available_slots: item.available_slots.join(", "),
    })),
    makeVenueRow
  );
  populateEditorTable(elements.preferencesBody, payload.preferences, makePreferenceRow);
  persistDraft();
}

function restoreDraft() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return false;
  }

  try {
    const draft = JSON.parse(raw);
    elements.budgetLimit.value = draft.budget_limit ?? "";
    elements.timeSlots.value = draft.time_slots ?? "";
    elements.changeInstruction.value = draft.change_instruction ?? "";
    populateEditorTable(
      elements.speakersBody,
      (draft.speakers || []).map((item) => ({
        ...item,
        available_slots: Array.isArray(item.available_slots)
          ? item.available_slots.join(", ")
          : item.available_slots,
      })),
      makeSpeakerRow
    );
    populateEditorTable(
      elements.venuesBody,
      (draft.venues || []).map((item) => ({
        ...item,
        available_slots: Array.isArray(item.available_slots)
          ? item.available_slots.join(", ")
          : item.available_slots,
      })),
      makeVenueRow
    );
    populateEditorTable(elements.preferencesBody, draft.preferences || [], makePreferenceRow);
    return true;
  } catch (error) {
    localStorage.removeItem(STORAGE_KEY);
    return false;
  }
}

function renderSummary(target, result) {
  target.innerHTML = "";
  [
    `Sessions: ${result.scheduled_sessions}`,
    `Budget Used: ${formatMoney(result.budget_used)}`,
    `Budget Remaining: ${formatMoney(result.budget_remaining)}`,
    `Attendees: ${result.scheduled_attendees}`,
  ].forEach((text) => {
    const pill = document.createElement("div");
    pill.className = "summary-pill";
    pill.textContent = text;
    target.appendChild(pill);
  });
}

function renderAssignments(target, assignments, editable = false) {
  target.innerHTML = "";
  if (!assignments.length) {
    const row = document.createElement("tr");
    row.innerHTML = "<td colspan='6'>No feasible assignments</td>";
    target.appendChild(row);
    return;
  }

  assignments.forEach((item) => {
    const row = document.createElement("tr");
    if (editable) {
      row.innerHTML = `
        <td><input type="text" value="${item.speaker}" autocomplete="off" spellcheck="false"></td>
        <td><input type="text" value="${item.venue}" autocomplete="off" spellcheck="false"></td>
        <td><input type="text" value="${item.slot}" autocomplete="off" spellcheck="false"></td>
        <td><input type="number" value="${item.speaker_cost + item.venue_cost}" autocomplete="off"></td>
        <td><input type="number" value="${item.attendee_score}" autocomplete="off"></td>
        <td><input type="number" value="${item.total_score}" autocomplete="off"></td>
      `;
    } else {
      row.innerHTML = `
        <td>${item.speaker}</td>
        <td>${item.venue}</td>
        <td>${item.slot}</td>
        <td>${formatMoney(item.speaker_cost + item.venue_cost)}</td>
        <td>${item.attendee_score}</td>
        <td>${item.total_score}</td>
      `;
    }
    target.appendChild(row);
  });
}

function renderReasoning(target, reasoning) {
  target.innerHTML = "";
  reasoning.forEach((item) => {
    const point = document.createElement("li");
    point.textContent = item;
    target.appendChild(point);
  });
}

function renderUnscheduled(target, unscheduled) {
  target.textContent = unscheduled.length
    ? unscheduled.map((item) => `${item.speaker}: ${item.reason}`).join(" | ")
    : "All speakers were scheduled successfully.";
}

function renderImpact(impact) {
  elements.impactGrid.innerHTML = "";
  [
    ["Change Applied", impact.change_applied],
    ["Session Delta", formatDelta(impact.delta_sessions)],
    ["Budget Delta", formatMoney(impact.delta_budget)],
    ["Attendee Delta", formatDelta(impact.delta_attendees)],
    ["Baseline Sessions", impact.baseline_sessions],
    ["Replanned Sessions", impact.replanned_sessions],
  ].forEach(([label, value]) => {
    const fragment = elements.impactCardTemplate.content.cloneNode(true);
    fragment.querySelector(".impact-label").textContent = label;
    fragment.querySelector(".impact-value").textContent = value;
    elements.impactGrid.appendChild(fragment);
  });

  elements.changeSummary.textContent = impact.change_applied;
}

function renderMetrics(result) {
  elements.metricSessions.textContent = result.scheduled_sessions;
  elements.metricBudget.textContent = formatMoney(result.budget_used);
  elements.metricAttendees.textContent = result.scheduled_attendees;
}

function renderResults(data) {
  renderMetrics(data.baseline);
  renderSummary(elements.baselineSummary, data.baseline);
  renderSummary(elements.replannedSummary, data.replanned);
  renderAssignments(elements.baselineTable, data.baseline.assignments, false);
  renderAssignments(elements.replannedTable, data.replanned.assignments, true);
  renderReasoning(elements.baselineReasoning, data.baseline.agent_reasoning);
  renderReasoning(elements.replannedReasoning, data.replanned.agent_reasoning);
  renderUnscheduled(elements.baselineUnscheduled, data.baseline.unscheduled);
  renderUnscheduled(elements.replannedUnscheduled, data.replanned.unscheduled);
  renderImpact(data.impact);
  elements.rawOutput.textContent = JSON.stringify(data, null, 2);
}

function setLoading(isLoading) {
  document.body.classList.toggle("is-loading", isLoading);
  elements.runPlanner.disabled = isLoading;
  elements.runPlanner.textContent = isLoading ? "Generating..." : "Generate AI Schedule";
}

function showError(message) {
  elements.changeSummary.textContent = message;
  elements.changeSummary.classList.add("is-error");
}

function clearError() {
  elements.changeSummary.classList.remove("is-error");
}

async function runPlanner() {
  clearError();
  setLoading(true);

  try {
    persistDraft();
    const payload = collectPayload();
    const response = await fetch(`${API_BASE}/api/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to generate plan.");
    }
    renderResults(data);
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
}

async function loadSample() {
  const response = await fetch(`${API_BASE}/api/sample`);
  const payload = await response.json();
  populateInputs(payload);
}

function handleTableActions(event) {
  const button = event.target.closest(".table-delete");
  if (!button) {
    return;
  }
  const row = button.closest("tr");
  const body = row.parentElement;
  row.remove();
  if (!body.children.length) {
    if (body === elements.speakersBody) {
      body.appendChild(makeSpeakerRow());
    } else if (body === elements.venuesBody) {
      body.appendChild(makeVenueRow());
    } else if (body === elements.preferencesBody) {
      body.appendChild(makePreferenceRow());
    }
  }
  persistDraft();
}

document.addEventListener("input", (event) => {
  if (event.target.matches("input")) {
    persistDraft();
  }
});

[elements.speakersBody, elements.venuesBody, elements.preferencesBody].forEach((body) => {
  body.addEventListener("click", handleTableActions);
});

[elements.budgetLimit, elements.timeSlots, elements.changeInstruction].forEach((element) => {
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
    }
  });
});

elements.addSpeaker.addEventListener("click", () => {
  elements.speakersBody.appendChild(makeSpeakerRow());
});

elements.addVenue.addEventListener("click", () => {
  elements.venuesBody.appendChild(makeVenueRow());
});

elements.addPreference.addEventListener("click", () => {
  elements.preferencesBody.appendChild(makePreferenceRow());
});

elements.loadSample.addEventListener("click", async () => {
  await loadSample();
  await runPlanner();
});

elements.runPlanner.addEventListener("click", runPlanner);

document.querySelectorAll(".chip").forEach((button) => {
  button.addEventListener("click", () => {
    elements.changeInstruction.value = button.dataset.change;
    persistDraft();
  });
});

window.addEventListener("DOMContentLoaded", async () => {
  const hasDraft = restoreDraft();
  if (!hasDraft) {
    await loadSample();
  }
  await runPlanner();
});
