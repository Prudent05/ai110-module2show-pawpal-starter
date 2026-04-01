"""
PawPal+ — CLI demo script.

Run with:  python main.py
Verifies that the Owner / Pet / Task / Scheduler classes work end-to-end.
"""

from datetime import date

from pawpal_system import (
    FREQ_DAILY,
    FREQ_WEEKLY,
    Owner,
    Pet,
    Scheduler,
    Task,
)

# ── 1. Create owner ────────────────────────────────────────────────────────
owner = Owner(name="Jordan", available_minutes=120)

# ── 2. Create pets ─────────────────────────────────────────────────────────
mochi = Pet(name="Mochi", species="dog", age=3, weight_kg=8.5,
            health_notes="Needs low-impact exercise")
luna = Pet(name="Luna", species="cat", age=5, weight_kg=4.2)

owner.add_pet(mochi)
owner.add_pet(luna)

# ── 3. Add tasks (intentionally out of time order) ─────────────────────────
mochi.add_task(Task(
    name="Evening walk",
    task_type="walk",
    duration_minutes=30,
    priority=4,
    scheduled_time="18:00",
    frequency=FREQ_DAILY,
    due_date=date.today(),
))
mochi.add_task(Task(
    name="Morning walk",
    task_type="walk",
    duration_minutes=20,
    priority=5,
    scheduled_time="07:30",
    frequency=FREQ_DAILY,
    due_date=date.today(),
))
mochi.add_task(Task(
    name="Heartworm meds",
    task_type="meds",
    duration_minutes=5,
    priority=5,
    scheduled_time="08:00",
    frequency=FREQ_WEEKLY,
    due_date=date.today(),
))
mochi.add_task(Task(
    name="Grooming session",
    task_type="grooming",
    duration_minutes=45,
    priority=2,
    scheduled_time="10:00",
))

luna.add_task(Task(
    name="Wet food feeding",
    task_type="feeding",
    duration_minutes=10,
    priority=5,
    scheduled_time="08:00",   # <-- same slot as Mochi's meds (conflict demo)
    frequency=FREQ_DAILY,
    due_date=date.today(),
))
luna.add_task(Task(
    name="Laser pointer play",
    task_type="enrichment",
    duration_minutes=15,
    priority=3,
    scheduled_time="19:00",
))
luna.add_task(Task(
    name="Vet check-up",
    task_type="vet",
    duration_minutes=60,
    priority=4,
    scheduled_time="11:00",
))

# ── 4. Build scheduler ─────────────────────────────────────────────────────
scheduler = Scheduler(owner)

# ── 5. Print today's schedule ──────────────────────────────────────────────
print("=" * 60)
print(scheduler.explain_plan())
print()

# ── 6. Chronological view (sorted by time) ────────────────────────────────
print("── All pending tasks in chronological order ──")
for task in scheduler.sort_by_time():
    print(f"  {task}")
print()

# ── 7. High-priority filter ───────────────────────────────────────────────
print("── High-priority tasks (P4+) ──")
for task in scheduler.filter_by_priority(4):
    print(f"  {task}")
print()

# ── 8. Mark a recurring daily task complete → spawns next occurrence ────────
print("── Completing 'Morning walk' (daily) ──")
morning_walk = mochi.tasks[1]  # index 1 in list
next_task = scheduler.mark_task_complete(mochi, morning_walk)
print(f"  Completed : {morning_walk.name} (status={morning_walk.completed})")
if next_task:
    print(f"  Next task created for: {next_task.due_date} — {next_task.name}")
print()

# ── 9. Conflict detection demo ────────────────────────────────────────────
print("── Conflict detection ──")
conflicts = scheduler.detect_conflicts()
if conflicts:
    for c in conflicts:
        print(f"  ⚠  {c}")
else:
    print("  No conflicts detected.")
print()

# ── 10. Filter by pet ────────────────────────────────────────────────────
print("── Luna's tasks ──")
for task in scheduler.filter_by_pet("Luna"):
    print(f"  {task}")
print("=" * 60)
