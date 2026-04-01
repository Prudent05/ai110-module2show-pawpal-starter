"""
PawPal+ — Logic Layer
All backend classes for the pet care scheduling system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care activity (walk, feeding, medication, etc.)."""

    name: str
    task_type: str          # e.g. "walk", "feeding", "meds", "grooming", "enrichment"
    duration_minutes: int
    priority: int           # 1 (low) – 5 (critical)
    completed: bool = False
    scheduled_time: Optional[str] = None  # e.g. "08:00"

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def reschedule(self, new_time: str) -> None:
        """Assign a new scheduled time slot to this task."""
        self.scheduled_time = new_time


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
        """Add a care task to this pet's list."""
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> None:
        """Remove a task by name (removes the first match)."""
        self.tasks = [t for t in self.tasks if t.name != task_name]

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.completed]


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Represents the pet owner who uses PawPal+."""

    name: str
    available_minutes: int  # total free time available today
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's profile."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name (removes the first match)."""
        self.pets = [p for p in self.pets if p.name != pet_name]


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Generates a daily care plan for all of an owner's pets.

    Strategy (to be implemented):
    - Collect all pending tasks across every pet.
    - Sort by priority (descending), then by duration (ascending) as a tiebreak.
    - Fit tasks into the owner's available time budget, stopping when time runs out.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def _all_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs for every incomplete task across all pets."""
        pairs: list[tuple[Pet, Task]] = []
        for pet in self.owner.pets:
            for task in pet.get_pending_tasks():
                pairs.append((pet, task))
        return pairs

    def generate_plan(self) -> list[Task]:
        """
        Build and return an ordered list of tasks that fit within
        the owner's available time, ranked by priority.
        """
        # TODO: implement scheduling algorithm
        pending = self._all_pending_tasks()
        # Sort: highest priority first; shortest duration as tiebreak
        pending.sort(key=lambda pt: (-pt[1].priority, pt[1].duration_minutes))

        plan: list[Task] = []
        time_used = 0
        for _pet, task in pending:
            if time_used + task.duration_minutes <= self.owner.available_minutes:
                plan.append(task)
                time_used += task.duration_minutes
        return plan

    def explain_plan(self) -> str:
        """
        Return a human-readable explanation of how the plan was constructed.
        """
        # TODO: implement explanation generation
        plan = self.generate_plan()
        if not plan:
            return "No tasks could be scheduled within the available time."

        lines = [
            f"Daily plan for {self.owner.name} "
            f"({self.owner.available_minutes} minutes available):\n"
        ]
        total = 0
        for i, task in enumerate(plan, start=1):
            lines.append(
                f"  {i}. [{task.priority}★] {task.name} "
                f"({task.duration_minutes} min)"
            )
            total += task.duration_minutes
        lines.append(f"\nTotal scheduled time: {total} min")
        return "\n".join(lines)

    def filter_by_priority(self, min_priority: int) -> list[Task]:
        """Return all pending tasks whose priority is >= min_priority."""
        return [
            task
            for _pet, task in self._all_pending_tasks()
            if task.priority >= min_priority
        ]
