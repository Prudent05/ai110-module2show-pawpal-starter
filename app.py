"""PawPal+ — Streamlit UI connected to the logic layer."""

import streamlit as st

from pawpal_system import (
    FREQ_DAILY,
    FREQ_ONCE,
    FREQ_WEEKLY,
    Owner,
    Pet,
    Scheduler,
    Task,
    TASK_EMOJIS,
)

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+")
st.caption("Your smart pet care daily planner.")

# ── Session state bootstrap ───────────────────────────────────────────────
# Streamlit re-runs the script on every interaction.
# We persist the Owner object in st.session_state so pet + task data
# survives between button clicks.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)

owner: Owner = st.session_state.owner

# ── Sidebar: owner & pet management ──────────────────────────────────────
with st.sidebar:
    st.header("👤 Owner Settings")
    new_name = st.text_input("Your name", value=owner.name)
    new_minutes = st.number_input(
        "Available time today (min)", min_value=10, max_value=1440, value=owner.available_minutes
    )
    if st.button("Save owner settings"):
        owner.name = new_name
        owner.available_minutes = int(new_minutes)
        st.success("Settings saved!")

    st.divider()
    st.header("🐾 Add a Pet")
    pet_name_in = st.text_input("Pet name", value="Mochi")
    species_in = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    age_in = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    weight_in = st.number_input("Weight (kg)", min_value=0.1, max_value=100.0,
                                value=5.0, step=0.1)
    notes_in = st.text_input("Health notes (optional)", value="")
    if st.button("Add pet"):
        existing = [p.name.lower() for p in owner.pets]
        if pet_name_in.lower() in existing:
            st.warning(f"'{pet_name_in}' already exists.")
        else:
            owner.add_pet(Pet(
                name=pet_name_in,
                species=species_in,
                age=int(age_in),
                weight_kg=float(weight_in),
                health_notes=notes_in,
            ))
            st.success(f"{pet_name_in} added!")

    if owner.pets:
        st.divider()
        st.header("🗑️ Remove a Pet")
        remove_name = st.selectbox("Select pet to remove",
                                   [p.name for p in owner.pets], key="remove_pet_select")
        if st.button("Remove pet"):
            owner.remove_pet(remove_name)
            st.success(f"{remove_name} removed.")

# ── Main area ─────────────────────────────────────────────────────────────
if not owner.pets:
    st.info("👈 Add at least one pet in the sidebar to get started.")
    st.stop()

# ── Add a task ────────────────────────────────────────────────────────────
st.subheader("➕ Add a Care Task")
col_pet, col_name, col_type = st.columns(3)
with col_pet:
    target_pet_name = st.selectbox("For pet", [p.name for p in owner.pets], key="task_pet")
with col_name:
    task_name_in = st.text_input("Task name", value="Morning walk")
with col_type:
    task_type_in = st.selectbox("Type", list(TASK_EMOJIS.keys()))

col_dur, col_pri, col_time, col_freq = st.columns(4)
with col_dur:
    duration_in = st.number_input("Duration (min)", min_value=1, max_value=480, value=20)
with col_pri:
    priority_in = st.slider("Priority (1=Low, 5=Critical)", 1, 5, 3)
with col_time:
    time_in = st.text_input("Time slot (HH:MM, optional)", value="")
with col_freq:
    freq_in = st.selectbox("Frequency", [FREQ_ONCE, FREQ_DAILY, FREQ_WEEKLY])

if st.button("Add task"):
    target_pet = next((p for p in owner.pets if p.name == target_pet_name), None)
    if target_pet:
        new_task = Task(
            name=task_name_in,
            task_type=task_type_in,
            duration_minutes=int(duration_in),
            priority=int(priority_in),
            scheduled_time=time_in.strip() if time_in.strip() else None,
            frequency=freq_in,
        )
        target_pet.add_task(new_task)
        st.success(f"Task '{task_name_in}' added to {target_pet_name}.")

st.divider()

# ── Per-pet task tables ───────────────────────────────────────────────────
st.subheader("📋 Current Tasks by Pet")
scheduler = Scheduler(owner)

for pet in owner.pets:
    with st.expander(f"{pet.name} — {pet.species}, {pet.age} yr", expanded=True):
        pending = pet.get_pending_tasks()
        done = pet.get_completed_tasks()
        if not pet.tasks:
            st.info("No tasks yet.")
            continue

        rows = []
        for task in scheduler.sort_by_time():
            # only tasks belonging to this pet
            if task not in pet.tasks:
                continue
            rows.append({
                "": task.emoji,
                "Task": task.name,
                "Time": task.scheduled_time or "—",
                "Duration": f"{task.duration_minutes} min",
                "Priority": f"P{task.priority} {task.priority_label}",
                "Frequency": task.frequency,
                "Status": "✓ Done" if task.completed else "○ Pending",
            })

        if rows:
            st.table(rows)

        # Mark-complete controls
        pending_names = [t.name for t in pending]
        if pending_names:
            mark_name = st.selectbox(
                "Mark complete", pending_names, key=f"mark_{pet.name}"
            )
            if st.button("✓ Mark done", key=f"btn_mark_{pet.name}"):
                task_obj = next((t for t in pending if t.name == mark_name), None)
                if task_obj:
                    next_t = scheduler.mark_task_complete(pet, task_obj)
                    msg = f"'{mark_name}' marked complete."
                    if next_t:
                        msg += f" Next occurrence created for {next_t.due_date}."
                    st.success(msg)

st.divider()

# ── Generate schedule ─────────────────────────────────────────────────────
st.subheader("📅 Generate Today's Schedule")
if st.button("Generate schedule", type="primary"):
    plan = scheduler.generate_plan()
    conflicts = scheduler.detect_conflicts()

    if conflicts:
        for c in conflicts:
            st.warning(f"⚠️ {c}")

    if not plan:
        st.error("No tasks fit within the available time budget.")
    else:
        total_min = sum(t.duration_minutes for t in plan)
        remaining = owner.available_minutes - total_min

        st.success(
            f"Scheduled **{len(plan)} tasks** using **{total_min} min** "
            f"of {owner.available_minutes} min available. "
            f"({remaining} min remaining)"
        )

        plan_rows = [
            {
                "": t.emoji,
                "Task": t.name,
                "Time": t.scheduled_time or "—",
                "Duration": f"{t.duration_minutes} min",
                "Priority": f"P{t.priority} {t.priority_label}",
            }
            for t in plan
        ]
        st.table(plan_rows)

        with st.expander("📝 Plain-language explanation"):
            st.text(scheduler.explain_plan())
