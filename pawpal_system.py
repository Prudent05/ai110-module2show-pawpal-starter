"""
PawPal+ — Logic Layer
All backend classes for the pet care scheduling system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

# Frequency constants
FREQ_ONCE = "once"
FREQ_DAILY = "daily"
FREQ_WEEKLY = "weekly"

PRIORITY_LABELS = {1: "Low", 2: "Low-Med", 3: "Medium", 4: "High", 5: "Critical"}
TASK_EMOJIS = {
    "walk": "🦮",
    "feeding": "🍖",
    "meds": "💊",
    "grooming": "✂️",
    "enrichment": "🎾",
    "vet": "🏥",
    "other": "📋",
}


@dataclass
class Task:
    """A single pet-care activity (walk, feeding, medication, etc.)."""

    name: str
    task_type: str          # e.g. "walk", "feeding", "meds", "grooming", "enrichment"
    duration_minutes: int
    priority: int           # 1 (low) – 5 (critical)
    completed: bool = False
    scheduled_time: Optional[str] = None   # "HH:MM" format, e.g. "08:00"
    frequency: str = FREQ_ONCE             # "once", "daily", or "weekly"
    due_date: Optional[date] = None        # used for recurrence tracking

    # ---- basic lifecycle -----------------------------------------------

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def reschedule(self, new_time: str) -> None:
        """Assign a new scheduled time slot ('HH:MM') to this task."""
        self.scheduled_time = new_time

    # ---- display helpers -----------------------------------------------

    @property
    def emoji(self) -> str:
        """Return a display emoji for this task type."""
        return TASK_EMOJIS.get(self.task_type, TASK_EMOJIS["other"])

    @property
    def priority_label(self) -> str:
        """Return a human-readable priority label."""
        return PRIORITY_LABELS.get(self.priority, str(self.priority))

    def __str__(self) -> str:
        """Return a concise single-line summary of the task."""
        time_str = f" @ {self.scheduled_time}" if self.scheduled_time else ""
        status = "✓" if self.completed else "○"
        return (
            f"[{status}] {self.emoji} {self.name}{time_str} "
            f"({self.duration_minutes} min | P{self.priority}-{self.priority_label})"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet whose care is being managed."""

    name: str
    species: str            # e.g. "dog", "cat", "rabbit"
    age: int                # years
    weight_kg: float
    health_notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a Task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> None:
        """Remove the first task whose name matches task_name."""
        self.tasks = [t for t in self.tasks if t.name != task_name]

    def get_pending_tasks(self) -> list[Task]:
        """Return all tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.completed]

    def get_completed_tasks(self) -> list[Task]:
        """Return all tasks that have been marked complete."""
        return [t for t in self.tasks if t.completed]

    def __str__(self) -> str:
        """Return a concise summary of this pet."""
        return (
            f"{self.name} ({self.species}, {self.age}yr, {self.weight_kg}kg)"
            + (f" — {self.health_notes}" if self.health_notes else "")
        )


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Represents the pet owner who uses PawPal+."""

    name: str
    available_minutes: int  # total care time available today (minutes)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet to this owner's profile."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove the first pet whose name matches pet_name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return (Pet, Task) pairs for every task across all pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def __str__(self) -> str:
        """Return a concise summary of this owner."""
        return (
            f"{self.name} | {self.available_minutes} min available | "
            f"{len(self.pets)} pet(s)"
        )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Generates and manages a daily care plan for all of an owner's pets.

    Core strategy:
    - Collect all pending tasks across every pet.
    - Sort by priority (highest first), then by scheduled time ('HH:MM') as a
      tiebreak so tasks with an explicit time slot are ordered chronologically.
    - Greedily fit tasks into the owner's available time budget.
    - After fitting, detect scheduling conflicts (duplicate 'HH:MM' slots).
    - Automatically spawn recurring replacements when a daily/weekly task is
      marked complete.
    """

    def __init__(self, owner: Owner) -> None:
        """Initialise the Scheduler with a reference to the owner."""
        self.owner = owner

    # ---- internal helpers -----------------------------------------------

    def _all_pending(self) -> list[tuple[Pet, Task]]:
        """Return (Pet, Task) pairs for every incomplete task across all pets."""
        return [
            (pet, task)
            for pet in self.owner.pets
            for task in pet.get_pending_tasks()
        ]

    # ---- sorting & filtering --------------------------------------------

    def sort_by_time(self) -> list[Task]:
        """
        Return all pending tasks sorted chronologically by scheduled_time.

        Tasks without a time slot are placed at the end.
        """
        pending = [task for _pet, task in self._all_pending()]
        return sorted(
            pending,
            key=lambda t: (t.scheduled_time is None, t.scheduled_time or ""),
        )

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks (pending and done) belonging to the named pet."""
        for pet in self.owner.pets:
            if pet.name.lower() == pet_name.lower():
                return list(pet.tasks)
        return []

    def filter_by_status(self, *, completed: bool) -> list[Task]:
        """Return all tasks across all pets that match the given completion status."""
        return [
            task
            for _pet, task in self.owner.get_all_tasks()
            if task.completed is completed
        ]

    def filter_by_priority(self, min_priority: int) -> list[Task]:
        """Return all pending tasks whose priority >= min_priority."""
        return [
            task
            for _pet, task in self._all_pending()
            if task.priority >= min_priority
        ]

    # ---- plan generation ------------------------------------------------

    def generate_plan(self) -> list[Task]:
        """
        Build and return an ordered list of tasks that fit within the owner's
        available time.

        Tasks are ranked by priority (highest first). Among tasks with the same
        priority, those with an earlier scheduled_time come first. Tasks that
        would exceed the remaining time budget are skipped.
        """
        pending = self._all_pending()
        pending.sort(
            key=lambda pt: (
                -pt[1].priority,
                pt[1].scheduled_time is None,
                pt[1].scheduled_time or "",
            )
        )

        plan: list[Task] = []
        time_used = 0
        for _pet, task in pending:
            if time_used + task.duration_minutes <= self.owner.available_minutes:
                plan.append(task)
                time_used += task.duration_minutes
        return plan

    def explain_plan(self) -> str:
        """
        Return a human-readable, formatted explanation of today's care plan.
        """
        plan = self.generate_plan()
        if not plan:
            return (
                f"No tasks fit within {self.owner.name}'s "
                f"{self.owner.available_minutes}-minute budget today."
            )

        lines = [
            f"═══ Today's PawPal+ Schedule for {self.owner.name} ═══",
            f"Available time : {self.owner.available_minutes} min",
            "",
        ]
        total = 0
        for i, task in enumerate(plan, start=1):
            time_str = f" @ {task.scheduled_time}" if task.scheduled_time else ""
            lines.append(
                f"  {i:>2}. {task.emoji} {task.name}{time_str} "
                f"— {task.duration_minutes} min  [P{task.priority} {task.priority_label}]"
            )
            total += task.duration_minutes

        remaining = self.owner.available_minutes - total
        lines += [
            "",
            f"Scheduled : {total} min",
            f"Remaining : {remaining} min",
        ]

        conflicts = self.detect_conflicts()
        if conflicts:
            lines += ["", "⚠️  Conflicts detected:"]
            for msg in conflicts:
                lines.append(f"   • {msg}")

        return "\n".join(lines)

    # ---- conflict detection ---------------------------------------------

    def detect_conflicts(self) -> list[str]:
        """
        Detect tasks in the current plan that share the same scheduled_time slot.

        Returns a list of warning strings (empty list = no conflicts).
        Only tasks that have an explicit scheduled_time are checked; tasks with
        no time slot are ignored (they don't conflict with anything).

        Note: This checks for exact-time collisions only, not overlapping
        durations — a deliberate tradeoff for simplicity.
        """
        plan = self.generate_plan()
        time_map: dict[str, list[Task]] = {}
        for task in plan:
            if task.scheduled_time:
                time_map.setdefault(task.scheduled_time, []).append(task)

        warnings: list[str] = []
        for slot, tasks in time_map.items():
            if len(tasks) > 1:
                names = ", ".join(t.name for t in tasks)
                warnings.append(f"Time {slot} has {len(tasks)} overlapping tasks: {names}")
        return warnings

    # ---- recurring tasks ------------------------------------------------

    def mark_task_complete(self, pet: Pet, task: Task) -> Optional[Task]:
        """
        Mark a task complete and, for recurring tasks, automatically create
        the next occurrence on the pet's task list.

        Returns the newly created Task for daily/weekly tasks, or None for
        one-off tasks.
        """
        task.mark_complete()

        if task.frequency == FREQ_ONCE:
            return None

        base_date = task.due_date or date.today()
        if task.frequency == FREQ_DAILY:
            next_due = base_date + timedelta(days=1)
        else:  # FREQ_WEEKLY
            next_due = base_date + timedelta(weeks=1)

        next_task = Task(
            name=task.name,
            task_type=task.task_type,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            completed=False,
            scheduled_time=task.scheduled_time,
            frequency=task.frequency,
            due_date=next_due,
        )
        pet.add_task(next_task)
        return next_task
