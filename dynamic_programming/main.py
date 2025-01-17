import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import random
from pulp import LpProblem, LpMinimize, LpVariable, lpSum
import matplotlib.pyplot as plt
import plotly.express as px

# hello
# Constants
DB_FILE = "tasks.db"

# Database functions
def init_db():
    """Initialize the database with necessary tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS Tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            TaskName TEXT NOT NULL,
            Day TEXT NOT NULL,
            StartTime TEXT NOT NULL,
            EndTime TEXT NOT NULL,
            Duration TEXT NOT NULL,
            NursesRequired INTEGER NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS Shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            StartTime TEXT NOT NULL,
            EndTime TEXT NOT NULL,
            BreakTime TEXT NOT NULL,
            BreakDuration TEXT NOT NULL,
            Weight FLOAT NOT NULL,
            Monday INT NOT NULL,
            Tuesday INT NOT NULL,
            Wednesday INT NOT NULL,
            Thursday INT NOT NULL,
            Friday INT NOT NULL,
            Saturday INT NOT NULL,
            Sunday INT NOT NULL,
            Flexibility TEXT NOT NULL,
            Notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_task_to_db(TaskName, Day, StartTime, EndTime, Duration, NursesRequired):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO Tasks (TaskName, Day, StartTime, EndTime, Duration, NursesRequired)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (TaskName, Day, StartTime, EndTime, Duration, NursesRequired))
    conn.commit()
    conn.close()

def add_shift_to_db(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO Shifts (
            StartTime, EndTime, BreakTime, BreakDuration, Weight,
            Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday,
            Flexibility, Notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()

def get_all(table):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df

def clear_all(table):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()

# Sidebar functions
def task_input_form():
    """Sidebar form to add a new task."""
    st.sidebar.header("Add Task")

    # Initialize session state for start and end time
    if "task_start_time" not in st.session_state:
        st.session_state["task_start_time"] = datetime.now().time()
    if "task_end_time" not in st.session_state:
        st.session_state["task_end_time"] = (datetime.now() + timedelta(hours=1)).time()

    # Task form inputs
    TaskName = st.sidebar.text_input("Task Name", "")
    Day = st.sidebar.selectbox("Day of the Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    StartTime = st.sidebar.time_input("Start Time", value=st.session_state["task_start_time"])
    EndTime = st.sidebar.time_input("End Time", value=st.session_state["task_end_time"])
    duration_hours = st.sidebar.number_input("Duration Hours", min_value=0, max_value=23, value=1)
    duration_minutes = st.sidebar.number_input("Duration Minutes", min_value=0, max_value=59, value=0)
    NursesRequired = st.sidebar.number_input("Nurses Required", min_value=1, value=1)

    # Update session state on user input
    st.session_state["task_start_time"] = StartTime
    st.session_state["task_end_time"] = EndTime

    # Add task button
    if st.sidebar.button("Add Task"):
        if TaskName:
            Duration = timedelta(hours=duration_hours, minutes=duration_minutes)
            add_task_to_db(
                TaskName,
                Day,
                f"{StartTime.hour}:{StartTime.minute}:00",
                f"{EndTime.hour}:{EndTime.minute}:00",
                str(Duration),
                NursesRequired
            )
            st.sidebar.success(f"Task '{TaskName}' added!")
        else:
            st.sidebar.error("Task name cannot be empty!")


def shift_input_form():
    """Sidebar form to add a new shift."""
    st.sidebar.header("Add Shift")

    # Session state for shift times
    if "shift_start_time" not in st.session_state:
        st.session_state["shift_start_time"] = datetime.now().time()
    if "shift_end_time" not in st.session_state:
        st.session_state["shift_end_time"] = (datetime.now() + timedelta(hours=1)).time()
    if "break_start_time" not in st.session_state:
        st.session_state["break_start_time"] = (datetime.now() + timedelta(hours=2)).time()

    Shift_StartTime = st.sidebar.time_input("Shift Start Time", value=st.session_state["shift_start_time"])
    Shift_EndTime = st.sidebar.time_input("Shift End Time", value=st.session_state["shift_end_time"])
    BreakTime = st.sidebar.time_input("Break Start Time", value=st.session_state["break_start_time"])
    BreakDuration_hours = st.sidebar.number_input("Break Duration Hours", min_value=0, max_value=23, value=0)
    BreakDuration_minutes = st.sidebar.number_input("Break Duration Minutes", min_value=0, max_value=59, value=30)
    Weight = st.sidebar.number_input("Shift Weight", min_value=0.0, value=1.0)

    Days = {day: st.sidebar.checkbox(day, value=(day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])) for day in
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
    Flexibility = st.sidebar.selectbox("Flexibility", options=["High", "Moderate", "Low"])
    Notes = st.sidebar.text_area("Additional Notes", "")

    if st.sidebar.button("Add Shift"):
        shift_data = (
            f"{Shift_StartTime.hour}:{Shift_StartTime.minute}:00",
            f"{Shift_EndTime.hour}:{Shift_EndTime.minute}:00",
            f"{BreakTime.hour}:{BreakTime.minute}:00",
            str(timedelta(hours=BreakDuration_hours, minutes=BreakDuration_minutes)),
            Weight,
            *(1 if Days[day] else 0 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
            Flexibility,
            Notes,
        )
        add_shift_to_db(shift_data)
        st.sidebar.success("Shift added successfully!")

def generate_and_fill_data(num_tasks=10, num_shifts=5):
    """Generate random tasks and shifts and populate the database."""
    # Initialize the database
    init_db()
    
    # Generate random tasks
    for _ in range(num_tasks):
        task_name = f"Task_{random.randint(1, 100)}"
        day = random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        start_time = datetime.now() + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
        duration = timedelta(hours=random.randint(0, 5), minutes=random.randint(0, 59))
        end_time = start_time + duration
        nurses_required = random.randint(1, 10)
        add_task_to_db(
            task_name,
            day,
            start_time.strftime("%H:%M:%S"),
            end_time.strftime("%H:%M:%S"),
            str(duration),
            nurses_required
        )

    # Generate random shifts
    for _ in range(num_shifts):
        start_time = datetime.now() + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
        end_time = start_time + timedelta(hours=random.randint(1, 8))
        break_time = start_time + timedelta(hours=random.randint(1, 3))
        break_duration = timedelta(minutes=random.randint(15, 60))
        weight = random.uniform(0.5, 2.0)
        days = {day: random.choice([0, 1]) for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
        flexibility = random.choice(["High", "Moderate", "Low"])
        notes = f"Random notes {random.randint(1, 100)}"
        shift_data = (
            start_time.strftime("%H:%M:%S"),
            end_time.strftime("%H:%M:%S"),
            break_time.strftime("%H:%M:%S"),
            str(break_duration),
            weight,
            *days.values(),
            flexibility,
            notes
        )
        add_shift_to_db(shift_data)

    st.success(f"Generated {num_tasks} tasks and {num_shifts} shifts successfully!")

def optimize_tasks_to_shifts():
    # Fetch data
    tasks_df = get_all("Tasks")
    shifts_df = get_all("Shifts")

    if tasks_df.empty or shifts_df.empty:
        st.error("Tasks or shifts data is missing. Add data and try again.")
        return

    # Prepare data
    tasks_df["StartTime"] = pd.to_datetime(tasks_df["StartTime"], format="%H:%M:%S").dt.time
    tasks_df["EndTime"] = pd.to_datetime(tasks_df["EndTime"], format="%H:%M:%S").dt.time
    shifts_df["StartTime"] = pd.to_datetime(shifts_df["StartTime"], format="%H:%M:%S").dt.time
    shifts_df["EndTime"] = pd.to_datetime(shifts_df["EndTime"], format="%H:%M:%S").dt.time

    # LP Problem
    problem = LpProblem("Task_Assignment", LpMinimize)

    # Decision Variables
    task_shift_vars = {}
    for task_id, task in tasks_df.iterrows():
        for shift_id, shift in shifts_df.iterrows():
            # Check if the shift can cover the task
            if (
                task["Day"] in shift.keys() and
                shift[task["Day"]] == 1 and
                shift["StartTime"] <= task["StartTime"] and
                shift["EndTime"] >= task["EndTime"]
            ):
                var_name = f"Task_{task_id}_Shift_{shift_id}"
                task_shift_vars[(task_id, shift_id)] = LpVariable(var_name, cat="Binary")

    # Objective Function: Minimize total shift weight
    problem += lpSum(
        task_shift_vars[(task_id, shift_id)] * shifts_df.loc[shift_id, "Weight"]
        for task_id, shift_id in task_shift_vars
    )

    # Constraints
    # 1. Each task must be assigned to at least one shift
    for task_id in tasks_df.index:
        problem += lpSum(
            task_shift_vars[(task_id, shift_id)]
            for shift_id in shifts_df.index if (task_id, shift_id) in task_shift_vars
        ) >= 1, f"Task_{task_id}_Coverage"

    # 2. Ensure shifts do not exceed their nurse capacity
    for shift_id in shifts_df.index:
        problem += lpSum(
            task_shift_vars[(task_id, shift_id)] * tasks_df.loc[task_id, "NursesRequired"]
            for task_id in tasks_df.index if (task_id, shift_id) in task_shift_vars
        ) <= shifts_df.loc[shift_id, "Monday"], f"Shift_{shift_id}_Capacity"

    # Solve the problem
    problem.solve()

    # Collect results
    results = []
    for (task_id, shift_id), var in task_shift_vars.items():
        if var.value() == 1:
            results.append({
                "TaskID": task_id,
                "ShiftID": shift_id,
                "TaskName": tasks_df.loc[task_id, "TaskName"],
                "ShiftStart": shifts_df.loc[shift_id, "StartTime"],
                "ShiftEnd": shifts_df.loc[shift_id, "EndTime"]
            })

    results_df = pd.DataFrame(results)

    # Check if all tasks are assigned
    assigned_tasks = results_df["TaskID"].unique()
    unassigned_tasks = tasks_df.loc[~tasks_df.index.isin(assigned_tasks)]
    if not unassigned_tasks.empty:
        st.warning("Some tasks could not be assigned:")
        st.dataframe(unassigned_tasks)
    else:
        st.success("All tasks successfully assigned!")

    # Display results
    if not results_df.empty:
        st.write("Optimal Task Assignments:")
        st.dataframe(results_df)
        st.download_button(
            label="Download Assignments as CSV",
            data=results_df.to_csv(index=False).encode("utf-8"),
            file_name="task_assignments.csv",
            mime="text/csv"
        )
    else:
        st.error("No feasible solution found.")

def optimize_tasks_to_shiftsv2():
    # Fetch data
    tasks_df = get_all("Tasks")
    shifts_df = get_all("Shifts")

    if tasks_df.empty or shifts_df.empty:
        st.error("Tasks or shifts data is missing. Add data and try again.")
        return

    # Prepare data
    tasks_df["StartTime"] = pd.to_datetime(tasks_df["StartTime"], format="%H:%M:%S").dt.time
    tasks_df["EndTime"] = pd.to_datetime(tasks_df["EndTime"], format="%H:%M:%S").dt.time
    shifts_df["StartTime"] = pd.to_datetime(shifts_df["StartTime"], format="%H:%M:%S").dt.time
    shifts_df["EndTime"] = pd.to_datetime(shifts_df["EndTime"], format="%H:%M:%S").dt.time

    # Helper function to check overlap
    def overlap(task, shift):
        task_start, task_end = task["StartTime"], task["EndTime"]
        shift_start, shift_end = shift["StartTime"], shift["EndTime"]
        break_start = datetime.strptime(shift["BreakTime"], "%H:%M:%S").time()
        break_end = (datetime.combine(datetime.today(), break_start) + pd.to_timedelta(shift["BreakDuration"])).time()

        # Check if task is within shift and not during the break
        return (
            shift_start <= task_start < shift_end and
            shift_start < task_end <= shift_end and
            not (task_start < break_end and task_end > break_start)
        )

    # LP Problem
    problem = LpProblem("Task_Assignment", LpMinimize)

    # Decision Variables
    task_shift_vars = {}
    nurse_shift_vars = {}
    for task_id, task in tasks_df.iterrows():
        for shift_id, shift in shifts_df.iterrows():
            if (
                shift[task["Day"]] == 1 and
                overlap(task, shift)
            ):
                var_name = f"Task_{task_id}_Shift_{shift_id}"
                task_shift_vars[(task_id, shift_id)] = LpVariable(var_name, cat="Binary")

    nurses = [f"Nurse_{i}" for i in range(len(shifts_df))]  # Assuming one nurse per shift max
    for nurse in nurses:
        for shift_id in shifts_df.index:
            var_name = f"Nurse_{nurse}_Shift_{shift_id}"
            nurse_shift_vars[(nurse, shift_id)] = LpVariable(var_name, cat="Binary")

    # Objective Function: Minimize total shift weight
    problem += lpSum(
        task_shift_vars[(task_id, shift_id)] * shifts_df.loc[shift_id, "Weight"]
        for task_id, shift_id in task_shift_vars
    )

    # Constraints
    # 1. Each task must be assigned to at least one shift
    for task_id in tasks_df.index:
        problem += lpSum(
            task_shift_vars[(task_id, shift_id)]
            for shift_id in shifts_df.index if (task_id, shift_id) in task_shift_vars
        ) >= 1, f"Task_{task_id}_Coverage"

    # 2. Ensure shifts do not exceed their nurse capacity
    for shift_id in shifts_df.index:
        problem += lpSum(
            task_shift_vars[(task_id, shift_id)] * tasks_df.loc[task_id, "NursesRequired"]
            for task_id in tasks_df.index if (task_id, shift_id) in task_shift_vars
        ) <= lpSum(
            nurse_shift_vars[(nurse, shift_id)] for nurse in nurses
        ), f"Shift_{shift_id}_Capacity"

    # 3. Assign each nurse to at most one shift
    for nurse in nurses:
        problem += lpSum(
            nurse_shift_vars[(nurse, shift_id)] for shift_id in shifts_df.index
        ) <= 1, f"Nurse_{nurse}_OneShift"

    # 4. Ensure a nurse is assigned to a shift only if tasks are assigned
    for shift_id in shifts_df.index:
        problem += lpSum(
            nurse_shift_vars[(nurse, shift_id)] for nurse in nurses
        ) >= lpSum(
            task_shift_vars[(task_id, shift_id)] for task_id in tasks_df.index if (task_id, shift_id) in task_shift_vars
        ), f"Shift_{shift_id}_HasNurse"

    # Solve the problem
    problem.solve()

    # Collect results
    task_results = []
    for (task_id, shift_id), var in task_shift_vars.items():
        if var.value() == 1:
            task_results.append({
                "TaskID": task_id,
                "ShiftID": shift_id,
                "TaskName": tasks_df.loc[task_id, "TaskName"],
                "ShiftStart": shifts_df.loc[shift_id, "StartTime"],
                "ShiftEnd": shifts_df.loc[shift_id, "EndTime"]
            })

    nurse_results = []
    for (nurse, shift_id), var in nurse_shift_vars.items():
        if var.value() == 1:
            nurse_results.append({
                "Nurse": nurse,
                "ShiftID": shift_id,
                "ShiftStart": shifts_df.loc[shift_id, "StartTime"],
                "ShiftEnd": shifts_df.loc[shift_id, "EndTime"]
            })

    task_results_df = pd.DataFrame(task_results)
    nurse_results_df = pd.DataFrame(nurse_results)

    # Check if all tasks are assigned
    assigned_tasks = task_results_df["TaskID"].unique()
    unassigned_tasks = tasks_df.loc[~tasks_df.index.isin(assigned_tasks)]
    if not unassigned_tasks.empty:
        st.warning("Some tasks could not be assigned:")
        st.dataframe(unassigned_tasks)
    else:
        st.success("All tasks successfully assigned!")

    # Display results
    if not task_results_df.empty:
        st.write("Optimal Task Assignments:")
        st.dataframe(task_results_df)
        st.download_button(
            label="Download Task Assignments as CSV",
            data=task_results_df.to_csv(index=False).encode("utf-8"),
            file_name="task_assignments.csv",
            mime="text/csv"
        )

    if not nurse_results_df.empty:
        st.write("Optimal Nurse Assignments:")
        st.dataframe(nurse_results_df)
        st.download_button(
            label="Download Nurse Assignments as CSV",
            data=nurse_results_df.to_csv(index=False).encode("utf-8"),
            file_name="nurse_assignments.csv",
            mime="text/csv"
        )
    else:
        st.error("No feasible nurse assignments found.")


def display_tasks_and_shifts():
    """Display tasks and shifts as Gantt charts with all days and hours displayed."""
    st.header("Visualize Tasks and Shifts for the Week")

    # Fetch data
    tasks_df = get_all("Tasks")
    shifts_df = get_all("Shifts")

    # Display tasks and shifts lists
    tasks_df = get_all("Tasks")
    shifts_df = get_all("Shifts")
    if not tasks_df.empty:
        st.write("**Tasks List**")
        st.dataframe(tasks_df)
        st.download_button(
            label="Download Tasks as CSV",
            data=tasks_df.to_csv(index=False).encode("utf-8"),
            file_name="tasks.csv",
            mime="text/csv"
        )


    if not shifts_df.empty:
        st.write("**Shifts List**")
        st.dataframe(shifts_df)
        st.download_button(
            label="Download Shifts as CSV",
            data=shifts_df.to_csv(index=False).encode("utf-8"),
            file_name="shifts.csv",
            mime="text/csv"
        )
    
    # Define the day order and the full hour range
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    full_day_range = ["2023-01-01 00:00:00", "2023-01-01 23:59:59"]

    # Prepare tasks DataFrame for visualization
    if not tasks_df.empty:
        # Add dummy date to Start and End times for compatibility
        tasks_df["Start"] = pd.to_datetime(f"2023-01-01 " + tasks_df["StartTime"], format="%Y-%m-%d %H:%M:%S")
        tasks_df["End"] = pd.to_datetime(f"2023-01-01 " + tasks_df["EndTime"], format="%Y-%m-%d %H:%M:%S")
        tasks_df["Day"] = pd.Categorical(tasks_df["Day"], categories=day_order, ordered=True)

        # Display tasks as a Gantt chart
        st.subheader("Tasks Schedule")
        fig_tasks = px.timeline(
            tasks_df,
            x_start="Start",
            x_end="End",
            y="Day",
            color="TaskName",
            title="Tasks Gantt Chart",
            labels={"Start": "Start Time", "End": "End Time", "Day": "Day of the Week", "TaskName": "Task"}
        )
        fig_tasks.update_yaxes(categoryorder="array", categoryarray=day_order)
        fig_tasks.update_xaxes(
            tickformat="%H:%M",
            dtick=3600000,  # One hour in milliseconds
            range=full_day_range  # Full 24-hour range
        )
        st.plotly_chart(fig_tasks)
    else:
        st.write("No tasks available to display.")

    # Prepare shifts DataFrame for visualization
    if not shifts_df.empty:
        # Add dummy date to Start and End times for compatibility
        shifts_df["Start"] = pd.to_datetime(f"2023-01-01 " + shifts_df["StartTime"], format="%Y-%m-%d %H:%M:%S")
        shifts_df["End"] = pd.to_datetime(f"2023-01-01 " + shifts_df["EndTime"], format="%Y-%m-%d %H:%M:%S")

        # Expand shifts for days they are active
        shift_expanded = []
        for _, row in shifts_df.iterrows():
            for day in day_order:
                if row[day] == 1:
                    shift_expanded.append({
                        "ShiftID": row["id"],
                        "Day": day,
                        "Start": row["Start"],
                        "End": row["End"]
                    })

        shifts_expanded_df = pd.DataFrame(shift_expanded)
        shifts_expanded_df["Day"] = pd.Categorical(shifts_expanded_df["Day"], categories=day_order, ordered=True)

        # Display shifts as a Gantt chart
        st.subheader("Shifts Schedule")
        fig_shifts = px.timeline(
            shifts_expanded_df,
            x_start="Start",
            x_end="End",
            y="Day",
            color="ShiftID",
            title="Shifts Gantt Chart",
            labels={"Start": "Start Time", "End": "End Time", "Day": "Day of the Week", "ShiftID": "Shift"}
        )
        fig_shifts.update_yaxes(categoryorder="array", categoryarray=day_order)
        fig_shifts.update_xaxes(
            tickformat="%H:%M",
            dtick=3600000,  # One hour in milliseconds
            range=full_day_range  # Full 24-hour range
        )
        st.plotly_chart(fig_shifts)
    else:
        st.write("No shifts available to display.")

# Main app
def main():
    init_db()
    st.header("Tools")

    # Input forms for adding tasks and shifts
    task_input_form()
    shift_input_form()

    # Create two columns for side-by-side buttons
    col1, col2 = st.columns(2)

    # Clear All Tasks button in the first column
    with col1:
        if st.button("Clear All Tasks"):
            clear_all("Tasks")
            st.success("All tasks have been cleared!")
            # Refresh tasks display
            tasks_df = get_all("Tasks")
            if tasks_df.empty:
                st.write("No tasks added yet.")
            else:
                st.write("**Tasks List**")
                st.dataframe(tasks_df)

    # Clear All Shifts button in the second column
    with col2:
        if st.button("Clear All Shifts"):
            clear_all("Shifts")
            st.success("All shifts have been cleared!")
            # Refresh shifts display
            shifts_df = get_all("Shifts")
            if shifts_df.empty:
                st.write("No shifts added yet.")
            else:
                st.write("**Shifts List**")
                st.dataframe(shifts_df)



    # Random data generation
    num_tasks = st.sidebar.number_input("Number of Tasks", min_value=0, max_value=100, value=10)
    num_shifts = st.sidebar.number_input("Number of Shifts", min_value=0, max_value=50, value=5)
    if st.sidebar.button("Generate Random Data"):
        generate_and_fill_data(num_tasks, num_shifts)

    # Visualize tasks and shifts
    display_tasks_and_shifts()

    # Optimization
    if st.button("Optimize Task Assignment"):
        optimize_tasks_to_shifts()
    # Optimization
    if st.button("Optimize Task Assignment V2"):
        optimize_tasks_to_shiftsv2()
if __name__ == "__main__":
    main()
