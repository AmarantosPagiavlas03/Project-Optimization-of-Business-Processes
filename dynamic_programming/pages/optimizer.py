import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from gurobipy import Model, GRB, quicksum
from database import get_all

# ------------------------------------------------------------------
#                     First Optimizer: Tasks-Shifts
# ------------------------------------------------------------------

def optimize_tasks_with_gurobi():
    """
    Assign tasks to (shift, day) pairs so that a single shift can have 
    different worker counts on different days.

    This version ensures that a Monday task won't force workers on Tuesday/Wednesday 
    if the shift is active multiple days.
    """

    # --- 1. Load Data ---
    tasks_df = get_all("TasksTable2")
    shifts_df = get_all("ShiftsTable5")

    # Basic check for empty data
    if tasks_df.empty or shifts_df.empty:
        st.error("Tasks or shifts data is missing. Add data and try again.")
        return

    # --- 2. Format Time Columns ---
    # Adjust your time format if it's not "%H:%M:%S"
    tasks_df["StartTime"] = pd.to_datetime(tasks_df["StartTime"], format="%H:%M:%S").dt.time
    tasks_df["EndTime"]   = pd.to_datetime(tasks_df["EndTime"],   format="%H:%M:%S").dt.time

    shifts_df["StartTime"] = pd.to_datetime(shifts_df["StartTime"], format="%H:%M:%S").dt.time
    shifts_df["EndTime"]   = pd.to_datetime(shifts_df["EndTime"],   format="%H:%M:%S").dt.time

    # Column names in ShiftsTable5 for the days of the week
    day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    # --- 3. Create Gurobi Model ---
    model = Model("Task_Assignment")

    # --- 4. Decision Variables ---
    # 4.1. Worker variables: (shift, day) -> integer # of workers
    shift_worker_vars = {}
    for shift_id, shift_row in shifts_df.iterrows():
        for day_str in day_names:
            if shift_row[day_str] == 1:  # shift is active on this day
                var_name = f"Workers_Shift_{shift_id}_{day_str}"
                shift_worker_vars[(shift_id, day_str)] = model.addVar(
                    vtype=GRB.INTEGER, lb=0, name=var_name
                )

    # 4.2. Task assignment variables: (task, shift, day) -> binary
    #      Only if the task's day == shift's active day AND times align
    task_shift_vars = {}
    for task_id, task_row in tasks_df.iterrows():
        t_day = task_row["Day"]   # e.g. "Monday"
        t_s   = task_row["StartTime"]
        t_e   = task_row["EndTime"]

        # Iterate over all shifts
        for shift_id, shift_row in shifts_df.iterrows():
            # Only consider if the shift is active on the task's day
            if shift_row[t_day] == 1:
                shift_s = shift_row["StartTime"]
                shift_e = shift_row["EndTime"]
                # Check if shift covers the task time
                if shift_s <= t_s and shift_e >= t_e:
                    var_name = f"Task_{task_id}_Shift_{shift_id}_{t_day}"
                    task_shift_vars[(task_id, shift_id, t_day)] = model.addVar(
                        vtype=GRB.BINARY, name=var_name
                    )

    # --- 5. Objective: Minimize total cost = sum(workers * weight) across (shift, day) ---
    model.setObjective(
        quicksum(
            shift_worker_vars[(s_id, d)] * shifts_df.loc[s_id, "Weight"]
            for (s_id, d) in shift_worker_vars
        ),
        GRB.MINIMIZE
    )

    # --- 6. Constraints ---

    # 6.1. Coverage: each task is assigned to at least one feasible (shift, day)
    for task_id, task_row in tasks_df.iterrows():
        # Gather all feasible assignment variables for this task
        feasible_assignments = [
            task_shift_vars[key]
            for key in task_shift_vars
            if key[0] == task_id  # same task
        ]
        # If there's at least one feasible shift-day, require that sum >= 1
        if feasible_assignments:
            model.addConstr(
                quicksum(feasible_assignments) >= 1,
                name=f"Task_{task_id}_Coverage"
            )
        else:
            # No feasible shift-day found: either data problem or the model is infeasible
            pass

    # 6.2. Worker capacity: for each (shift, day), total nurses required
    #     by tasks assigned cannot exceed the # of workers assigned
    for (shift_id, day_str) in shift_worker_vars:
        model.addConstr(
            quicksum(
                tasks_df.loc[t_id, "NursesRequired"] * task_shift_vars[(t_id, shift_id, day_str)]
                for (t_id, s_id, d) in task_shift_vars
                if s_id == shift_id and d == day_str
            ) <= shift_worker_vars[(shift_id, day_str)],
            name=f"Shift_{shift_id}_{day_str}_WorkerCap"
        )

    # # 6.2. Worker capacity: for each (shift, day), total nurses required
    # #     by tasks assigned cannot exceed the # of workers assigned
    # for (shift_id, day_str) in shift_worker_vars:
    #     model.addConstr(
    #         quicksum(
    #             task_shift_vars[(t_id-1, shift_id, day_str)] + task_shift_vars[(t_id, shift_id, day_str)]
    #             for (t_id, s_id, d) in task_shift_vars
    #             if s_id == shift_id and d == day_str and tasks_df.loc[t_id-1, "EndTime"] <= tasks_df.loc[t_id, "StartTime"]
    #         ) <= 1,
    #         name=f"Shift_{shift_id}_{day_str}"
    #     )

    # --- 7. Solve the model ---
    with st.spinner("Optimizing tasks and shifts. Please wait..."):
        model.optimize()

    # --- 8. Collect and Display Results ---
    if model.status == GRB.OPTIMAL:
        # Build a list of assignment results
        results = []
        day_summary = {}

        for (task_id, shift_id, d), assign_var in task_shift_vars.items():
            if assign_var.x > 0.5:
                workers_assigned = shift_worker_vars.get((shift_id, d), 0).x
                # Optional cost breakdown
                total_assigned_tasks = sum(
                    task_shift_vars[(tid, shift_id, d)].x > 0.5
                    for tid in tasks_df.index
                    if (tid, shift_id, d) in task_shift_vars
                )
                # shift_weight = shifts_df.loc[shift_id, "Weight"]
                if total_assigned_tasks > 0 and workers_assigned > 0:
                    # cost_per_task = shift_weight / total_assigned_tasks
                    # task_duration = (t_e - t_s).total_seconds()
                    # shift_duration = (shift_e - shift_s).total_seconds()
                    # duration_ratio = task_duration / shift_duration
                    # task_cost = cost_per_task * duration_ratio * (
                    #     tasks_df.loc[task_id, "NursesRequired"] / workers_assigned
                    # )
                    task_cost = 0

                else:
                    task_cost = 0

                results.append({
                    "TaskID": tasks_df.loc[task_id, "id"],
                    "ShiftID": shifts_df.loc[shift_id, "id"],
                    "Day": d,
                    "TaskName": tasks_df.loc[task_id, "TaskName"],
                    "TaskStart": tasks_df.loc[task_id, "StartTime"],
                    "TaskEnd": tasks_df.loc[task_id, "EndTime"],
                    "ShiftStart": shifts_df.loc[shift_id, "StartTime"],
                    "ShiftEnd": shifts_df.loc[shift_id, "EndTime"],
                    "WorkersNeededForShiftDay": workers_assigned,
                    "TaskCost": task_cost,
                    "VariableAssign": assign_var.x
                })

                # Update daily summary
                if d not in day_summary:
                    day_summary[d] = {"TotalCost": 0, "NumTasks": 0, "NumWorkers": 0}
                day_summary[d]["TotalCost"]  += task_cost
                day_summary[d]["NumTasks"]   += 1
                day_summary[d]["NumWorkers"] += workers_assigned

        # Convert to DataFrame
        results_df = pd.DataFrame(results)

        if not results_df.empty:
            st.success("Task-shift-day optimization successful!")
            st.balloons()

            day_summary_df = pd.DataFrame.from_dict(day_summary, orient="index").reset_index()
            day_summary_df.columns = ["Day", "TotalCost", "NumTasks", "NumWorkers"]

            st.write("**Optimal Task Assignments with Worker Counts**")
            st.dataframe(results_df, hide_index=True)

            st.download_button(
                label="Download Assignments as CSV",
                data=results_df.to_csv(index=False).encode("utf-8"),
                file_name="task_assignments_with_workers.csv",
                mime="text/csv"
            )

            st.write("**Daily Summary of Costs, Tasks, and Workers**")
            st.dataframe(day_summary_df, hide_index=True)

            st.download_button(
                label="Download Daily Summary as CSV",
                data=day_summary_df.to_csv(index=False).encode("utf-8"),
                file_name="daily_summary.csv",
                mime="text/csv"
            )
        else:
            st.error("No tasks were assigned (results empty).")

    else:
        st.error(f"Optimization failed with status: {model.status}")
        # Diagnose infeasibility, if needed
        model.computeIIS()
        for constr in model.getConstrs():
            if constr.IISConstr:
                st.write(f"Infeasible Constraint: {constr.constrName}")

# ------------------------------------------------------------------
#                Second Optimizer: Assign Workers
# ------------------------------------------------------------------
def optimize_workers_for_shifts():
    """
    Assign actual workers to the shifts from the first optimization.
    We know how many workers each shift needs. Now we decide which
    worker goes where, based on each worker’s day/time preferences.
    """
    # 1. Read needed data
    shifts_df = get_all("ShiftsTable5")
    workers_df = get_all("Workers")

    # The shift_worker_vars from the first optimization are not stored in DB,
    # but we do have the final integer result for each shift’s needed worker count
    # from the results CSV or from the model. Typically you'd store that in a table,
    # or re-run in memory. For this example, let's define a new column in ShiftsTable5
    # if you want (or we just pretend we have it). Instead, we will re-derive it from
    # the existing approach or just ask the user to enter "how many workers does each shift need?"

    # For demonstration, let's say the user manually enters a minimal coverage requirement
    # for each shift (like "1" or "2" or "3"). Alternatively, you can read the results
    # from a CSV or store them in a table. The code below checks for a column "NeededWorkers"
    # in ShiftsTable5. If missing, we fallback to a user-provided input.

    if "NeededWorkers" not in shifts_df.columns:
        st.info("**No 'NeededWorkers' column found in ShiftsTable5.**")
        st.write("We will assume each shift needs coverage from the first optimization or a user input.")
        needed_workers_inputs = {}
        for i, row in shifts_df.iterrows():
            shift_label = f"Shift ID {row['id']} ({row['StartTime']} - {row['EndTime']})"
            needed_workers_inputs[i] = st.number_input(
                f"Workers needed for {shift_label}",
                min_value=0, value=1, step=1
            )
        # Store the results in a new column for the model usage
        shifts_df["NeededWorkers"] = shifts_df.index.map(needed_workers_inputs)
    else:
        st.success("Found 'NeededWorkers' column in ShiftsTable5. Using existing data.")

    # Prepare time fields for comparison
    # Convert day preference for each worker to time
    # Convert shift start/end to time
    # Then a worker can staff a shift on a given day if shift’s time is within the worker’s preference.
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def parse_time_str(t_str):
        # "HH:MM:SS" -> time object
        return datetime.strptime(t_str, "%H:%M:%S").time()

    # Convert shift times
    shifts_df["StartTime"] = shifts_df["StartTime"].apply(parse_time_str)
    shifts_df["EndTime"]   = shifts_df["EndTime"].apply(parse_time_str)

    # Build a dictionary for each worker's availability: worker_availability[worker_id][day] = (start, end)
    worker_availability = {}
    for _, w in workers_df.iterrows():
        w_id = w["id"]
        worker_availability[w_id] = {}
        for day in day_names:
            start_col = day + "Start"
            end_col   = day + "End"
            # Some columns might be None if the user didn't specify
            # Default to a small window or 00:00-00:00 if empty
            if w[start_col] is not None and w[end_col] is not None:
                w_start = parse_time_str(w[start_col])
                w_end   = parse_time_str(w[end_col])
            else:
                w_start, w_end = datetime.strptime("00:00:00", "%H:%M:%S").time(), datetime.strptime("00:00:00", "%H:%M:%S").time()
            worker_availability[w_id][day] = (w_start, w_end)

    # Create new Gurobi Model
    model = Model("Worker_Assignment")

    # Decision variable x[w, s]: 1 if worker w is assigned to shift s, 0 otherwise
    x = {}
    for s_idx, s_row in shifts_df.iterrows():
        for w_idx, w_row in workers_df.iterrows():
            # For each day, if the shift is active on that day (==1), check if worker is available
            # A shift can be active on multiple days (like you have multiple day columns),
            # but typically it's "1 shift per day." We'll gather all days that are set to 1 in that shift row.
            # If ANY day is valid, we might allow assignment. Usually you'd do a per-day shift approach.
            # For simplicity, let’s assume each shift row is for a single day or
            # we only allow assignment if the worker is available for *every* day indicated. 
            # You may choose the logic that fits your scenario.
            can_work_this_shift = False
            for day in day_names:
                if s_row[day] == 1:
                    # Check time overlap with worker’s preference
                    w_start, w_end = worker_availability[w_row["id"]][day]
                    shift_start, shift_end = s_row["StartTime"], s_row["EndTime"]
                    # We'll do a simple “shift must be fully within worker's preference window”
                    # or the worker can't do it.
                    if (w_start <= shift_start) and (shift_end <= w_end):
                        can_work_this_shift = True
                    else:
                        # If worker is not available for ANY active day, break
                        can_work_this_shift = False
                        break

            if can_work_this_shift:
                var_name = f"x_{w_idx}_{s_idx}"
                x[(w_idx, s_idx)] = model.addVar(vtype=GRB.BINARY, name=var_name)
            else:
                # Worker can't do that shift
                pass

    # Objective: We want to ensure coverage, possibly with minimal “uncovered seats.”
    # We'll create a slack variable for each shift indicating how many seats are unfilled.
    # Then we minimize the sum of these slacks.
    slack = {}
    for s_idx, s_row in shifts_df.iterrows():
        shift_id = s_row["id"]
        slack[s_idx] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"slack_{shift_id}")

    model.setObjective(quicksum(slack[s_idx] for s_idx in shifts_df.index), GRB.MINIMIZE)

    # Constraints
    # 1. The number of workers assigned to shift s plus slack >= needed workers
    for s_idx, s_row in shifts_df.iterrows():
        shift_id = s_row["id"]
        needed = s_row["NeededWorkers"]
        assigned_sum = quicksum(
            x[(w_idx, s_idx)] for (w_idx, sh_idx) in x.keys() if sh_idx == s_idx
        )
        model.addConstr(
            assigned_sum + slack[s_idx] >= needed,
            name=f"coverage_shift_{shift_id}"
        )

    # 2. Each worker can only do one shift per day (if you want to enforce that).
    #    If a shift covers multiple days, that gets more complicated. For simplicity,
    #    we’ll assume each shift is effectively on one day or only one shift can be assigned for that worker per day.
    #    Implementation approach: For each worker w, for each day d, sum of x[w, s for that day] <= 1.
    for w_idx in workers_df.index:
        for day in day_names:
            # All shifts that are active on 'day'
            shifts_on_day = [
                s_idx for s_idx, s_row in shifts_df.iterrows()
                if s_row[day] == 1
            ]
            # sum(x[w_idx, s_idx]) <= 1
            model.addConstr(
                quicksum(x[(w_idx, s_idx)]
                         for s_idx in shifts_on_day
                         if (w_idx, s_idx) in x) <= 1,
                name=f"worker_{w_idx}_{day}_limit"
            )

    with st.spinner("Optimizing worker assignment..."):
        model.optimize()

    if model.status == GRB.OPTIMAL:
        st.success("Worker assignment optimization successful!")
        st.balloons()

        results = []
        for (w_idx, s_idx), var in x.items():
            if var.x > 0.5:
                # That means worker w_idx is assigned to shift s_idx
                w_name = workers_df.loc[w_idx, "WorkerName"]
                s_id   = shifts_df.loc[s_idx, "id"]
                needed = shifts_df.loc[s_idx, "NeededWorkers"]
                s_start = shifts_df.loc[s_idx, "StartTime"]
                s_end   = shifts_df.loc[s_idx, "EndTime"]
                # Identify which day(s) the shift is for
                # We can store them for clarity
                shift_days = []
                for day in day_names:
                    if shifts_df.loc[s_idx, day] == 1:
                        shift_days.append(day)
                results.append({
                    "WorkerID": w_idx,
                    "WorkerName": w_name,
                    "ShiftTableID": s_id,
                    "ShiftDays": ", ".join(shift_days),
                    "ShiftStart": s_start,
                    "ShiftEnd": s_end,
                    "NeededWorkers": needed
                })

        results_df = pd.DataFrame(results)
        if not results_df.empty:
            st.write("**Worker Assignments**")
            st.dataframe(results_df)

            st.download_button(
                label="Download Worker Assignments as CSV",
                data=results_df.to_csv(index=False).encode("utf-8"),
                file_name="worker_assignments.csv",
                mime="text/csv"
            )

        else:
            st.error("No worker assignments found. Possibly the preferences are too restrictive.")
    else:
        st.error(f"Worker assignment optimization failed with status: {model.status}")

