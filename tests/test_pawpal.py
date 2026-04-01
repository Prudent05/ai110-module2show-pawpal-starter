"""
PawPal+ automated test suite.

Run with:  python -m pytest
"""

from datetime import date, timedelta

import pytest

from pawpal_system import (
    FREQ_DAILY,
    FREQ_ONCE,
    FREQ_WEEKLY,
    Owner,
    Pet,
    Scheduler,
    Task,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def basic_pet():
    """A dog with no initial tasks."""
    return Pet(name="Mochi", species="dog", age=3, weight_kg=8.5)


@pytest.fixture
def basic_owner(basic_pet):
    """An owner with 120 minutes available and one pet."""
    owner = Owner(name="Jordan", available_minutes=120)
    owner.add_pet(basic_pet)
    return owner


@pytest.fixture
def scheduler(basic_owner):
    """A Scheduler backed by basic_owner."""
    return Scheduler(basic_owner)


# ── Task: mark_complete ───────────────────────────────────────────────────

class TestTaskCompletion:
    def test_mark_complete_changes_status(self):
        """mark_complete() sets completed to True."""
        task = Task(name="Walk", task_type="walk", duration_minutes=20, priority=3)
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True

    def test_mark_complete_is_idempotent(self):
        """Calling mark_complete() twice does not raise and stays True."""
        task = Task(name="Walk", task_type="walk", duration_minutes=20, priority=3)
        task.mark_complete()
        task.mark_complete()
        assert task.completed is True


# ── Pet: task management ─────────────────────────────────────────────────

class TestPetTaskManagement:
    def test_add_task_increases_count(self, basic_pet):
        """Adding a task to a Pet increases its task count by 1."""
        before = len(basic_pet.tasks)
        basic_pet.add_task(Task(name="Feed", task_type="feeding",
                                duration_minutes=10, priority=5))
        assert len(basic_pet.tasks) == before + 1

    def test_remove_task_decreases_count(self, basic_pet):
        """Removing a task by name decreases task count by 1."""
        task = Task(name="Feed", task_type="feeding", duration_minutes=10, priority=5)
        basic_pet.add_task(task)
        before = len(basic_pet.tasks)
        basic_pet.remove_task("Feed")
        assert len(basic_pet.tasks) == before - 1

    def test_get_pending_excludes_completed(self, basic_pet):
        """get_pending_tasks() only returns incomplete tasks."""
        t1 = Task(name="Walk", task_type="walk", duration_minutes=20, priority=3)
        t2 = Task(name="Meds", task_type="meds", duration_minutes=5, priority=5)
        t1.mark_complete()
        basic_pet.add_task(t1)
        basic_pet.add_task(t2)
        pending = basic_pet.get_pending_tasks()
        assert t2 in pending
        assert t1 not in pending


# ── Scheduler: sorting ───────────────────────────────────────────────────

class TestSortByTime:
    def test_tasks_returned_in_chronological_order(self, basic_pet, scheduler):
        """sort_by_time() returns tasks ordered earliest scheduled_time first."""
        basic_pet.add_task(Task(name="Evening walk", task_type="walk",
                                duration_minutes=30, priority=4, scheduled_time="18:00"))
        basic_pet.add_task(Task(name="Morning walk", task_type="walk",
                                duration_minutes=20, priority=5, scheduled_time="07:30"))
        basic_pet.add_task(Task(name="Midday meds", task_type="meds",
                                duration_minutes=5, priority=5, scheduled_time="12:00"))

        sorted_tasks = scheduler.sort_by_time()
        times = [t.scheduled_time for t in sorted_tasks if t.scheduled_time]
        assert times == sorted(times)

    def test_tasks_without_time_go_last(self, basic_pet, scheduler):
        """Tasks with no scheduled_time appear after tasks with a time slot."""
        basic_pet.add_task(Task(name="Walk", task_type="walk",
                                duration_minutes=20, priority=5, scheduled_time="07:00"))
        basic_pet.add_task(Task(name="Play", task_type="enrichment",
                                duration_minutes=15, priority=3))  # no time

        sorted_tasks = scheduler.sort_by_time()
        assert sorted_tasks[-1].scheduled_time is None


# ── Scheduler: conflict detection ────────────────────────────────────────

class TestConflictDetection:
    def test_no_conflicts_when_times_differ(self, basic_owner, scheduler):
        """detect_conflicts() returns empty list when all slots are distinct."""
        pet = basic_owner.pets[0]
        pet.add_task(Task(name="Walk", task_type="walk",
                          duration_minutes=20, priority=5, scheduled_time="07:00"))
        pet.add_task(Task(name="Feed", task_type="feeding",
                          duration_minutes=10, priority=5, scheduled_time="08:00"))
        assert scheduler.detect_conflicts() == []

    def test_conflict_flagged_for_same_time_slot(self, basic_owner):
        """detect_conflicts() returns a warning when two tasks share a time slot."""
        pet = basic_owner.pets[0]
        pet.add_task(Task(name="Meds", task_type="meds",
                          duration_minutes=5, priority=5, scheduled_time="08:00"))
        pet.add_task(Task(name="Feed", task_type="feeding",
                          duration_minutes=10, priority=5, scheduled_time="08:00"))
        scheduler = Scheduler(basic_owner)
        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) == 1
        assert "08:00" in conflicts[0]


# ── Scheduler: recurrence ────────────────────────────────────────────────

class TestRecurringTasks:
    def test_daily_task_creates_next_occurrence(self, basic_pet, scheduler):
        """Completing a daily task spawns a new task due tomorrow."""
        today = date.today()
        task = Task(
            name="Daily walk",
            task_type="walk",
            duration_minutes=20,
            priority=5,
            frequency=FREQ_DAILY,
            due_date=today,
        )
        basic_pet.add_task(task)
        count_before = len(basic_pet.tasks)

        next_task = scheduler.mark_task_complete(basic_pet, task)

        assert task.completed is True
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert len(basic_pet.tasks) == count_before + 1

    def test_weekly_task_creates_occurrence_in_seven_days(self, basic_pet, scheduler):
        """Completing a weekly task spawns a new task due in 7 days."""
        today = date.today()
        task = Task(
            name="Grooming",
            task_type="grooming",
            duration_minutes=45,
            priority=3,
            frequency=FREQ_WEEKLY,
            due_date=today,
        )
        basic_pet.add_task(task)
        next_task = scheduler.mark_task_complete(basic_pet, task)

        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)

    def test_once_task_does_not_create_recurrence(self, basic_pet, scheduler):
        """Completing a once-off task does NOT create a follow-up task."""
        task = Task(
            name="Vet visit",
            task_type="vet",
            duration_minutes=60,
            priority=4,
            frequency=FREQ_ONCE,
        )
        basic_pet.add_task(task)
        count_before = len(basic_pet.tasks)
        result = scheduler.mark_task_complete(basic_pet, task)

        assert result is None
        assert len(basic_pet.tasks) == count_before


# ── Scheduler: generate_plan – time budget ───────────────────────────────

class TestGeneratePlan:
    def test_plan_respects_time_budget(self, basic_owner):
        """generate_plan() never exceeds the owner's available_minutes."""
        pet = basic_owner.pets[0]
        pet.add_task(Task(name="A", task_type="walk",
                          duration_minutes=50, priority=5))
        pet.add_task(Task(name="B", task_type="walk",
                          duration_minutes=50, priority=5))
        pet.add_task(Task(name="C", task_type="walk",
                          duration_minutes=50, priority=5))  # 150 min total > 120

        scheduler = Scheduler(basic_owner)
        plan = scheduler.generate_plan()
        total = sum(t.duration_minutes for t in plan)
        assert total <= basic_owner.available_minutes

    def test_plan_empty_when_no_tasks(self, scheduler):
        """generate_plan() returns an empty list when there are no pending tasks."""
        plan = scheduler.generate_plan()
        assert plan == []

    def test_high_priority_task_scheduled_before_low(self, basic_owner):
        """Higher-priority tasks appear before lower-priority tasks in the plan."""
        pet = basic_owner.pets[0]
        pet.add_task(Task(name="Low", task_type="enrichment",
                          duration_minutes=20, priority=1))
        pet.add_task(Task(name="High", task_type="meds",
                          duration_minutes=20, priority=5))

        scheduler = Scheduler(basic_owner)
        plan = scheduler.generate_plan()

        names = [t.name for t in plan]
        assert names.index("High") < names.index("Low")
