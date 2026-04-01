# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

Run the CLI demo:

```bash
python main.py
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## Smarter Scheduling

PawPal+ implements the following algorithmic capabilities beyond a basic task list:

| Feature | Description |
|---------|-------------|
| **Priority-first scheduling** | Tasks are ranked by priority (1–5). Higher-priority tasks are always scheduled before lower ones and fit into the owner's time budget greedily. |
| **Chronological sorting** | `Scheduler.sort_by_time()` orders all pending tasks by their `HH:MM` time slot. Tasks without an explicit time appear at the end. |
| **Filtering** | `filter_by_pet()`, `filter_by_status()`, and `filter_by_priority()` let you slice the task list by any dimension. |
| **Recurring tasks** | Tasks flagged as `daily` or `weekly` automatically spawn the next occurrence when marked complete, using Python's `timedelta`. |
| **Conflict detection** | `Scheduler.detect_conflicts()` identifies tasks in the plan that share the same `HH:MM` slot and returns plain-language warning messages rather than crashing. |

---

## Testing PawPal+

Run the full automated test suite:

```bash
python -m pytest
```

Tests live in `tests/test_pawpal.py` and cover:

- **Task completion** — `mark_complete()` correctly flips `completed` to `True`
- **Task addition** — adding a task to a `Pet` increases its task count
- **Sorting correctness** — tasks are returned in chronological `HH:MM` order
- **Recurrence logic** — daily tasks get a new occurrence due tomorrow; weekly tasks get one due in 7 days; once-off tasks do not recur
- **Conflict detection** — duplicate time slots are correctly flagged
- **Time-budget respect** — `generate_plan()` never exceeds `available_minutes`
- **Priority ordering** — higher-priority tasks appear before lower-priority ones

**Confidence level: ⭐⭐⭐⭐ (4/5)**
The core scheduling behaviors are well covered. Edge cases to explore next: a pet with zero tasks, tasks whose combined duration exactly equals the budget, and graceful handling of malformed time strings.

---

## 📸 Demo

<!-- Replace the placeholder below with your own screenshot once the app is running -->
<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank">
  <img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' />
</a>

