import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import random
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
import matplotlib.pyplot as plt
import plotly.express as px
from gurobipy import Model, GRB, quicksum

DB_FILE = "tasksv2.db"


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
        CREATE TABLE IF NOT EXISTS ShiftsTable1 (
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
        INSERT INTO ShiftsTable1 (
            StartTime, EndTime, BreakTime, BreakDuration, Weight,
            Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, Notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

def task_input_form():
    """Sidebar form to add a new task."""
    with st.sidebar.expander("Add Task", expanded=False):
        # Initialize session state for start and end time
        if "task_start_time" not in st.session_state:
            st.session_state["task_start_time"] = datetime.now().time()
        if "task_end_time" not in st.session_state:
            st.session_state["task_end_time"] = (datetime.now() + timedelta(hours=1)).time()

        # Task form inputs
        TaskName = st.text_input("Task Name", "")
        Day = st.selectbox("Day of the Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        StartTime = st.time_input("Start Time", value=st.session_state["task_start_time"])
        EndTime = st.time_input("End Time", value=st.session_state["task_end_time"])
        duration_hours = st.number_input("Duration Hours", min_value=0, max_value=23, value=1)
        duration_minutes = st.number_input("Duration Minutes", min_value=0, max_value=59, value=0)
        NursesRequired = st.number_input("Nurses Required", min_value=1, value=1)

        # Update session state on user input
        st.session_state["task_start_time"] = StartTime
        st.session_state["task_end_time"] = EndTime

        # Add task button
        if st.button("Add Task"):
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
                st.success(f"Task '{TaskName}' added!")
            else:
                st.error("Task name cannot be empty!")

def shift_input_form():
    """Sidebar form to add a new shift."""
    with st.sidebar.expander("Add Shift", expanded=False):
        # Session state for shift times
        if "shift_start_time" not in st.session_state:
            st.session_state["shift_start_time"] = datetime.now().time()
        if "shift_end_time" not in st.session_state:
            st.session_state["shift_end_time"] = (datetime.now() + timedelta(hours=1)).time()
        if "break_start_time" not in st.session_state:
            st.session_state["break_start_time"] = (datetime.now() + timedelta(hours=2)).time()

        # Shift form inputs
        Shift_StartTime = st.time_input("Shift Start Time", value=st.session_state["shift_start_time"])
        Shift_EndTime = st.time_input("Shift End Time", value=st.session_state["shift_end_time"])
        BreakTime = st.time_input("Break Start Time", value=st.session_state["break_start_time"])
        BreakDuration_hours = st.number_input("Break Duration Hours", min_value=0, max_value=23, value=0)
        BreakDuration_minutes = st.number_input("Break Duration Minutes", min_value=0, max_value=59, value=30)
        Weight = st.number_input("Shift Weight", min_value=0.0, value=1.0)

        Days = {day: st.checkbox(day, value=(day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])) for day in
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
        Notes = st.text_area("Additional Notes", "")

        # Add shift button
        if st.button("Add Shift"):
            shift_data = (
                f"{Shift_StartTime.hour}:{Shift_StartTime.minute}:00",
                f"{Shift_EndTime.hour}:{Shift_EndTime.minute}:00",
                f"{BreakTime.hour}:{BreakTime.minute}:00",
                str(timedelta(hours=BreakDuration_hours, minutes=BreakDuration_minutes)),
                Weight,
                *(1 if Days[day] else 0 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
                Notes,
            )
            add_shift_to_db(shift_data)
            st.success("Shift added successfully!")


def generate_and_fill_data_form():
    """Sidebar form to generate and fill random data."""
    with st.sidebar.expander("Generate Random Data", expanded=False):
        st.write("Generate random tasks and shifts to populate the database.")

        # Input fields for number of tasks and shifts
        num_tasks = st.number_input("Number of Tasks", min_value=1, value=10, step=1)
        num_shifts = st.number_input("Number of Shifts", min_value=1, value=5, step=1)

        # Button to trigger data generation
        if st.button("Generate Data"):
            # Call the data generation function
            generate_and_fill_data(num_tasks=int(num_tasks), num_shifts=int(num_shifts))
            st.success(f"Generated {num_tasks} tasks and {num_shifts} shifts successfully!")

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

        notes = f"Random notes {random.randint(1, 100)}"
        shift_data = (
            start_time.strftime("%H:%M:%S"),
            end_time.strftime("%H:%M:%S"),
            break_time.strftime("%H:%M:%S"),
            str(break_duration),
            weight,
            *days.values(),
            notes
        )
        add_shift_to_db(shift_data)


def insert():
    

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
INSERT INTO Tasks (
    TaskName,
    Day,
    StartTime,
    EndTime,
    Duration,
    NursesRequired
)
VALUES
    ('Dressing Change', 'Monday', '07:30:00', '07:45:00', 15, 1),
    ('Vital Signs Monitoring', 'Monday', '10:30:00', '11:00:00', 30, 2),
    ('Wound Care', 'Monday', '14:30:00', '15:15:00', 45, 3),
    ('Medication Administration', 'Monday', '22:00:00', '22:30:00', 30, 2),
    ('Physical Therapy', 'Tuesday', '08:00:00', '08:45:00', 45, 2),
    ('Dressing Change', 'Tuesday', '13:30:00', '13:45:00', 15, 1),
    ('Vital Signs Monitoring', 'Tuesday', '16:00:00', '16:30:00', 30, 2),
    ('Medication Administration', 'Tuesday', '21:30:00', '22:00:00', 30, 2),
    ('Wound Care', 'Wednesday', '07:30:00', '08:15:00', 45, 3),
    ('Physical Therapy', 'Wednesday', '12:00:00', '12:45:00', 45, 2),
    ('Dressing Change', 'Wednesday', '18:00:00', '18:15:00', 15, 1),
    ('Vital Signs Monitoring', 'Thursday', '09:00:00', '09:30:00', 30, 2),
    ('Medication Administration', 'Thursday', '13:00:00', '13:30:00', 30, 2),
    ('Wound Care', 'Thursday', '17:30:00', '18:15:00', 45, 3),
    ('Dressing Change', 'Friday', '07:30:00', '07:45:00', 15, 1),
    ('Vital Signs Monitoring', 'Friday', '14:30:00', '15:00:00', 30, 2),
    ('Medication Administration', 'Friday', '21:30:00', '22:00:00', 30, 2),
    ('Wound Care', 'Saturday', '09:30:00', '10:15:00', 45, 3),
    ('Physical Therapy', 'Saturday', '14:00:00', '14:45:00', 45, 2),
    ('Vital Signs Monitoring', 'Saturday', '20:00:00', '20:30:00', 30, 2),
    ('Dressing Change', 'Sunday', '14:30:00', '14:45:00', 15, 1),
    ('Wound Care', 'Sunday', '20:00:00', '20:45:00', 45, 3);


    ''')
    conn.commit()
    conn.close()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
   INSERT INTO ShiftsTable1 (
    StartTime,
    EndTime,
    BreakTime,
    BreakDuration,
    Weight,
    Monday,
    Tuesday,
    Wednesday,
    Thursday,
    Friday,
    Saturday,
    Sunday,
    Notes
)
VALUES
    ('07:00:00', '15:00:00', '11:00:00', '0:30:00', 1200, 1, 1, 1, 1, 1, 0, 0, 'Morning shift'),
    ('15:00:00', '23:00:00', '19:00:00', '0:30:00', 1400, 1, 1, 1, 1, 1, 1, 1, 'Evening shift'),
    ('23:00:00', '07:00:00', '03:00:00', '0:30:00', 1600, 1, 1, 1, 1, 1, 1, 1, 'Night shift'),
    ('08:00:00', '14:00:00', '12:00:00', '0:20:00', 1000, 1, 1, 1, 1, 1, 0, 0, 'Short morning shift'),
    ('14:00:00', '20:00:00', '17:00:00', '0:30:00', 1100, 1, 1, 1, 1, 1, 1, 1, 'Afternoon shift'),
    ('20:00:00', '02:00:00', '23:00:00', '0:20:00', 1300, 0, 1, 1, 1, 1, 1, 1, 'Evening/night hybrid shift'),
    ('09:00:00', '17:00:00', '13:00:00', '0:45:00', 1500, 1, 1, 0, 1, 1, 0, 0, 'Standard day shift'),
    ('06:00:00', '14:00:00', '10:00:00', '0:30:00', 1100, 1, 1, 1, 1, 1, 1, 0, 'Early morning shift'),
    ('14:00:00', '22:00:00', '18:00:00', '0:30:00', 1200, 1, 1, 1, 1, 1, 1, 1, 'Full afternoon-evening shift'),
    ('10:00:00', '18:00:00', '13:30:00', '0:30:00', 1300, 1, 1, 1, 1, 1, 0, 0, 'Midday to evening shift');


    ''')
    conn.commit()
    conn.close()

def optimize_tasks_with_gurobi():
    # Fetch data
    tasks_df = get_all("Tasks")
    shifts_df = get_all("ShiftsTable1")

    if tasks_df.empty or shifts_df.empty:
        st.error("Tasks or shifts data is missing. Add data and try again.")
        return

    # Convert time to comparable format
    tasks_df["StartTime"] = pd.to_datetime(tasks_df["StartTime"], format="%H:%M:%S").dt.time
    tasks_df["EndTime"] = pd.to_datetime(tasks_df["EndTime"], format="%H:%M:%S").dt.time
    shifts_df["StartTime"] = pd.to_datetime(shifts_df["StartTime"], format="%H:%M:%S").dt.time
    shifts_df["EndTime"] = pd.to_datetime(shifts_df["EndTime"], format="%H:%M:%S").dt.time

    # Create Gurobi Model
    model = Model("Task_Assignment")

    # Decision Variables
    task_shift_vars = {}
    shift_worker_vars = {}

    for task_id, task in tasks_df.iterrows():
        for shift_id, shift in shifts_df.iterrows():
            # Check if the shift can cover the task
            if (
                shift[task["Day"]] == 1 and
                shift["StartTime"] <= task["StartTime"] and
                shift["EndTime"] >= task["EndTime"]
            ):
                var_name = f"Task_{task_id}_Shift_{shift_id}"
                task_shift_vars[(task_id, shift_id)] = model.addVar(
                    vtype=GRB.BINARY, name=var_name
                )

    for shift_id in shifts_df.index:
        shift_worker_vars[shift_id] = model.addVar(
            vtype=GRB.INTEGER, lb=0, name=f"Workers_Shift_{shift_id}"
        )

    # Objective Function: Minimize total cost
    model.setObjective(
        quicksum(
            shift_worker_vars[shift_id] * shifts_df.loc[shift_id, "Weight"]
            for shift_id in shifts_df.index
        ),
        GRB.MINIMIZE
    )

    # Constraints
    # 1. Each task must be assigned to at least one shift
    for task_id in tasks_df.index:
        model.addConstr(
            quicksum(
                task_shift_vars[(task_id, shift_id)]
                for shift_id in shifts_df.index if (task_id, shift_id) in task_shift_vars
            ) >= 1,
            name=f"Task_{task_id}_Coverage"
        )

    # 2. Workers per shift must satisfy all assigned tasks' nurse requirements
    for shift_id in shifts_df.index:
        model.addConstr(
            quicksum(
                task_shift_vars[(task_id, shift_id)] * tasks_df.loc[task_id, "NursesRequired"]
                for task_id in tasks_df.index if (task_id, shift_id) in task_shift_vars
            ) <= shift_worker_vars[shift_id],
            name=f"Shift_{shift_id}_Workers"
        )

    # Optimize the model
    with st.spinner("Optimizing tasks and shifts. Please wait..."):
        model.optimize()


    # Collect results
    if model.status == GRB.OPTIMAL:
        st.success("Optimization successful!")
        st.balloons()
        results = []
        day_summary = {}

        for (task_id, shift_id), var in task_shift_vars.items():
            if var.x > 0.5:  # Binary variable is 1
                task_day = tasks_df.loc[task_id, "Day"]
                # Calculate task cost
                total_tasks_in_shift = sum(
                    task_shift_vars[(task_id, shift_id)].x > 0.5
                    for task_id in tasks_df.index if (task_id, shift_id) in task_shift_vars
                )

                if total_tasks_in_shift > 0:
                    shift_cost_per_task = shifts_df.loc[shift_id, "Weight"] / total_tasks_in_shift
                    task_cost = shift_cost_per_task * (tasks_df.loc[task_id, "NursesRequired"] / shift_worker_vars[shift_id].x)
                else:
                    task_cost = 0  # No tasks assigned to this shift

                workers_assigned = shift_worker_vars[shift_id].x

                # Add to results
                # Add to results
                results.append({
                    "TaskID": task_id,
                    "ShiftID": shift_id,
                    "TaskName": tasks_df.loc[task_id, "TaskName"],
                    "TaskDay": task_day,
                    "TaskStart": tasks_df.loc[task_id, "StartTime"],
                    "TaskEnd": tasks_df.loc[task_id, "EndTime"],
                    "ShiftStart": shifts_df.loc[shift_id, "StartTime"],
                    "ShiftEnd": shifts_df.loc[shift_id, "EndTime"],
                    "ShiftNotes": shifts_df.loc[shift_id, "Notes"],
                    "WorkersAssigned": workers_assigned,
                    "Cost": task_cost
                })


                # Update day summary
                if task_day not in day_summary:
                    day_summary[task_day] = {"TotalCost": 0, "NumTasks": 0, "NumWorkers": 0}
                day_summary[task_day]["TotalCost"] += task_cost
                day_summary[task_day]["NumTasks"] += 1
                day_summary[task_day]["NumWorkers"] += workers_assigned  # Sum workers

        # Create DataFrame for results
        results_df = pd.DataFrame(results)
        day_summary_df = pd.DataFrame.from_dict(day_summary, orient="index").reset_index()
        day_summary_df.columns = ["Day", "TotalCost", "NumTasks", "NumWorkers"]

        if not results_df.empty:
            # Display results
            st.write("Optimal Task Assignments with Worker Counts:")
            st.dataframe(results_df)

            # Download assignments as CSV
            st.download_button(
                label="Download Assignments as CSV",
                data=results_df.to_csv(index=False).encode("utf-8"),
                file_name="task_assignments_with_workers.csv",
                mime="text/csv"
            )

            # Display and download the day summary table
            st.write("Daily Summary of Costs, Tasks, and Workers:")
            st.dataframe(day_summary_df)

            st.download_button(
                label="Download Daily Summary as CSV",
                data=day_summary_df.to_csv(index=False).encode("utf-8"),
                file_name="daily_summary.csv",
                mime="text/csv"
            )
        else:
            st.error("No feasible solution found.")
    else:
        st.error(f"Optimization failed with status: {model.status}")
        model.computeIIS()
        for constr in model.getConstrs():
            if constr.IISConstr:
                st.write(f"Infeasible Constraint: {constr.constrName}")

def display_tasks_and_shifts():
    """Display tasks and shifts as Gantt charts with all days and hours displayed."""
    st.header("Visualize Tasks and Shifts for the Week")

    # Display tasks and shifts lists
    tasks_df = get_all("Tasks")
    shifts_df = get_all("ShiftsTable1")
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
    generate_and_fill_data_form()


    # Add an empty placeholder to create space dynamically
    spacer = st.sidebar.empty()  # Create an empty widget to act as a spacer

    # Add "Clear All Tasks" and "Clear All Shifts" buttons in the sidebar at the bottom
    with st.sidebar:
        st.markdown("---")  # Add a separator line

        # Two columns for side-by-side buttons
        col1, col2 = st.columns(2)

        # Clear All Tasks button
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

        # Clear All Shifts button
        with col2:
            if st.button("Clear All Shifts"):
                clear_all("ShiftsTable1")
                st.success("All shifts have been cleared!")
                # Refresh shifts display
                shifts_df = get_all("ShiftsTable1")
                if shifts_df.empty:
                    st.write("No shifts added yet.")
                else:
                    st.write("**Shifts List**")
                    st.dataframe(shifts_df)

    # Use the empty placeholder to add dynamic space
    spacer.markdown("<br><br><br>", unsafe_allow_html=True) 

 

    # Optimization
    if st.button("Data Example"):
        insert()
    if st.button("Optimize Task Assignment"):
        optimize_tasks_with_gurobi()
    # Visualize tasks and shifts
    display_tasks_and_shifts()


if __name__ == "__main__":
    main()
