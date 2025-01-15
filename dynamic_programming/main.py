import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import random
# from pulp import LpProblem, LpMinimize, LpVariable, lpSum


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
    TaskName = st.sidebar.text_input("Task Name", "")
    Day = st.sidebar.selectbox("Day of the Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    StartTime = st.sidebar.time_input("Start Time", value=datetime.now().time())
    EndTime = st.sidebar.time_input("End Time", value=datetime.now().time())
    duration_hours = st.sidebar.number_input("Duration Hours", min_value=0, max_value=23, value=1)
    duration_minutes = st.sidebar.number_input("Duration Minutes", min_value=0, max_value=59, value=0)
    NursesRequired = st.sidebar.number_input("Nurses Required", min_value=1, value=1)

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

    Shift_StartTime = st.sidebar.time_input("Shift Start Time", value=st.session_state["shift_start_time"])
    Shift_EndTime = st.sidebar.time_input("Shift End Time", value=st.session_state["shift_end_time"])
    BreakTime = st.sidebar.time_input("Break Start Time", value=(datetime.now() + timedelta(hours=2)).time())
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

# def optimize_tasks_to_shifts():
#     # Fetch tasks and shifts data
#     tasks_df = get_all("Tasks")
#     shifts_df = get_all("Shifts")

#     # Ensure data exists
#     if tasks_df.empty or shifts_df.empty:
#         st.error("Tasks or shifts data is missing. Add data and try again.")
#         return

#     # Problem definition
#     problem = LpProblem("Task_Assignment", LpMinimize)

#     # Convert start and end times to datetime for easier comparison
#     tasks_df["StartTime"] = pd.to_datetime(tasks_df["StartTime"], format="%H:%M:%S").dt.time
#     tasks_df["EndTime"] = pd.to_datetime(tasks_df["EndTime"], format="%H:%M:%S").dt.time
#     shifts_df["StartTime"] = pd.to_datetime(shifts_df["StartTime"], format="%H:%M:%S").dt.time
#     shifts_df["EndTime"] = pd.to_datetime(shifts_df["EndTime"], format="%H:%M:%S").dt.time

#     # Create decision variables for task-shift assignments
#     task_shift_vars = {}
#     for task_id, task in tasks_df.iterrows():
#         for shift_id, shift in shifts_df.iterrows():
#             # Check if the task and shift overlap in time and day
#             if (
#                 task["Day"] in shift.keys() and
#                 shift[task["Day"]] == 1 and  # Shift is available on task day
#                 shift["StartTime"] <= task["StartTime"] and
#                 shift["EndTime"] >= task["EndTime"]
#             ):
#                 var_name = f"Assign_Task_{task_id}_to_Shift_{shift_id}"
#                 task_shift_vars[(task_id, shift_id)] = LpVariable(var_name, cat="Binary")

#     # Objective Function: Minimize total shift weight for all assignments
#     problem += lpSum(
#         task_shift_vars[(task_id, shift_id)] * shifts_df.loc[shift_id, "Weight"]
#         for task_id, shift_id in task_shift_vars
#     )

#     # Constraints
#     # 1. Each task must be assigned to at least one shift
#     for task_id in tasks_df.index:
#         problem += lpSum(
#             task_shift_vars[(task_id, shift_id)]
#             for shift_id in shifts_df.index if (task_id, shift_id) in task_shift_vars
#         ) >= 1, f"Task_{task_id}_Assigned"

#     # 2. A shift cannot exceed its nurse capacity
#     for shift_id in shifts_df.index:
#         problem += lpSum(
#             task_shift_vars[(task_id, shift_id)] * tasks_df.loc[task_id, "NursesRequired"]
#             for task_id in tasks_df.index if (task_id, shift_id) in task_shift_vars
#         ) <= shifts_df.loc[shift_id, "Monday"], f"Shift_{shift_id}_Capacity"

#     # Solve the problem
#     problem.solve()

#     # Collect results
#     results = []
#     for (task_id, shift_id), var in task_shift_vars.items():
#         if var.value() == 1:
#             results.append({
#                 "TaskID": task_id,
#                 "ShiftID": shift_id,
#                 "TaskName": tasks_df.loc[task_id, "TaskName"],
#                 "ShiftStart": shifts_df.loc[shift_id, "StartTime"],
#                 "ShiftEnd": shifts_df.loc[shift_id, "EndTime"]
#             })

#     results_df = pd.DataFrame(results)

#     # Display results
#     if results_df.empty:
#         st.write("No feasible solution found.")
#     else:
#         st.write("Optimal Task Assignment:")
#         st.dataframe(results_df)
#         st.download_button(
#             label="Download Assignment as CSV",
#             data=results_df.to_csv(index=False).encode("utf-8"),
#             file_name="task_shift_assignment.csv",
#             mime="text/csv"
#         )

# Main app
def main():
    init_db()
    st.title("Task Scheduler with SQLite Persistence")

    task_input_form()
    shift_input_form()

    st.header("Tasks List")
    tasks_df = get_all("Tasks")
    if not tasks_df.empty:
        st.dataframe(tasks_df)
        st.download_button(
            label="Download Tasks as CSV",
            data=tasks_df.to_csv(index=False).encode("utf-8"),
            file_name="tasks.csv",
            mime="text/csv"
        )
    else:
        st.write("No tasks added yet.")

    if st.button("Clear All Tasks"):
        clear_all("Tasks")
        st.success("All tasks have been cleared!")

    st.header("Shifts List")
    shifts_df = get_all("Shifts")
    if not shifts_df.empty:
        st.dataframe(shifts_df)
        st.download_button(
            label="Download Shifts as CSV",
            data=shifts_df.to_csv(index=False).encode("utf-8"),
            file_name="shifts.csv",
            mime="text/csv"
        )
    else:
        st.write("No shifts added yet.")

    if st.button("Clear All Shifts"):
        clear_all("Shifts")
        st.success("All shifts have been cleared!")

    if st.sidebar.button("Generate Random Data"):
        num_tasks = st.sidebar.number_input("Number of Tasks", min_value=1, max_value=100, value=10)
        num_shifts = st.sidebar.number_input("Number of Shifts", min_value=1, max_value=50, value=5)
        generate_and_fill_data(num_tasks, num_shifts)

    # if st.button("Optimize Task Assignment"):
        # optimize_tasks_to_shifts()
if __name__ == "__main__":
    main()
