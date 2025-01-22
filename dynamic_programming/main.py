import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import random
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
import plotly.express as px
from gurobipy import Model, GRB, quicksum
from datetime import time

DB_FILE = "tasksv2.db"


# ------------------------------------------------------------------
#                           Database
# ------------------------------------------------------------------
def init_db():
    """
    Initialize the database with necessary tables.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Table: Tasks
    c.execute('''
        CREATE TABLE IF NOT EXISTS TasksTable1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            TaskName TEXT NOT NULL,
            Day TEXT NOT NULL,
            StartTime TEXT NOT NULL,
            EndTime TEXT NOT NULL,
            Duration TEXT NOT NULL,
            NursesRequired INTEGER NOT NULL
        )
    ''')

    # Table: Shifts
    c.execute('''
    CREATE TABLE IF NOT EXISTS ShiftsTable3 (
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

        Notes TEXT,

        -- Add day-specific columns for needed workers
        MondayNeeded INT DEFAULT 0,
        TuesdayNeeded INT DEFAULT 0,
        WednesdayNeeded INT DEFAULT 0,
        ThursdayNeeded INT DEFAULT 0,
        FridayNeeded INT DEFAULT 0,
        SaturdayNeeded INT DEFAULT 0,
        SundayNeeded INT DEFAULT 0
    );
    ''')

    # Table: Workers
    c.execute('''
        CREATE TABLE IF NOT EXISTS Workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            WorkerName TEXT NOT NULL,
            MondayStart TEXT,
            MondayEnd TEXT,
            TuesdayStart TEXT,
            TuesdayEnd TEXT,
            WednesdayStart TEXT,
            WednesdayEnd TEXT,
            ThursdayStart TEXT,
            ThursdayEnd TEXT,
            FridayStart TEXT,
            FridayEnd TEXT,
            SaturdayStart TEXT,
            SaturdayEnd TEXT,
            SundayStart TEXT,
            SundayEnd TEXT
        )
    ''')

    conn.commit()
    conn.close()


# -------------------------- DB Helpers ---------------------------
def add_task_to_db(TaskName, Day, StartTime, EndTime, Duration, NursesRequired):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO TasksTable1 (TaskName, Day, StartTime, EndTime, Duration, NursesRequired)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (TaskName, Day, StartTime, EndTime, Duration, NursesRequired))
    conn.commit()
    conn.close()


def add_shift_to_db(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO ShiftsTable3 (
            StartTime, EndTime, BreakTime, BreakDuration, Weight,
            Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, Notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()


def add_worker_to_db(
    worker_name,
    mon_start, mon_end,
    tue_start, tue_end,
    wed_start, wed_end,
    thu_start, thu_end,
    fri_start, fri_end,
    sat_start, sat_end,
    sun_start, sun_end
):
    """
    Insert a new worker into the Workers table.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO Workers (
            WorkerName,
            MondayStart, MondayEnd,
            TuesdayStart, TuesdayEnd,
            WednesdayStart, WednesdayEnd,
            ThursdayStart, ThursdayEnd,
            FridayStart, FridayEnd,
            SaturdayStart, SaturdayEnd,
            SundayStart, SundayEnd
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        worker_name,
        mon_start, mon_end,
        tue_start, tue_end,
        wed_start, wed_end,
        thu_start, thu_end,
        fri_start, fri_end,
        sat_start, sat_end,
        sun_start, sun_end
    ))
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

def update_needed_workers_for_each_day(results_df):
    """
    Use the first-optimization assignments (results_df) to populate
    MondayNeeded, TuesdayNeeded, ... columns for each ShiftID in ShiftsTable3.
    """
    if results_df.empty:
        st.error("No results to update needed workers. `results_df` is empty.")
        return
    print("Columns in results_df:", results_df.columns)

    required_columns = ["ShiftID", "TaskDay", "WorkersNeededForShift"]
    missing_columns = [col for col in required_columns if col not in results_df.columns]
    if missing_columns:
        st.error(f"Missing required columns in results_df: {missing_columns}")
        return
    
    # 1. Aggregate how many workers are needed for each (ShiftID, Day).
    #    If a single shift has multiple tasks on the same day, you might 
    #    want sum() or max(). That depends on your logic. Let's use max() here.
    shift_day_needs = (
        results_df
        .groupby(["ShiftID", "TaskDay"])["WorkersNeededForShift"]
        .max()  # or .sum()
        .reset_index()
    )
    # 2. Build a dictionary: shift_day_dict[shift_id][day] = needed count
    day_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    shift_day_dict = {}

    for _, row in shift_day_needs.iterrows():
        sid = row["ShiftID"]
        day = row["TaskDay"]         # e.g. "Monday"
        needed = int(row["WorkersNeededForShift"])

        if sid not in shift_day_dict:
            shift_day_dict[sid] = {d: 0 for d in day_list}  # default 0 for each day

        # Assign the needed count for that day
        shift_day_dict[sid][day] = needed
 
    # 3. Update ShiftsTable3 for each shift ID
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    for sid, day_map in shift_day_dict.items():
        c.execute('''
            UPDATE ShiftsTable3
            SET
              MondayNeeded    = :mon,
              TuesdayNeeded   = :tue,
              WednesdayNeeded = :wed,
              ThursdayNeeded  = :thu,
              FridayNeeded    = :fri,
              SaturdayNeeded  = :sat,
              SundayNeeded    = :sun
            WHERE id = :shift_id
        ''', {
            "mon": day_map["Monday"],
            "tue": day_map["Tuesday"],
            "wed": day_map["Wednesday"],
            "thu": day_map["Thursday"],
            "fri": day_map["Friday"],
            "sat": day_map["Saturday"],
            "sun": day_map["Sunday"],
            "shift_id": sid
        })

    conn.commit()
    conn.close()

    st.success("Day-specific NeededWorkers columns have been updated in ShiftsTable3!")



# ------------------------------------------------------------------
#                         Form Inputs
# ------------------------------------------------------------------

def generate_time_intervals():
    intervals = [time(hour=h, minute=m) for h in range(24) for m in range(0, 60, 15)]
    intervals.append(time(0, 0))  # Add 24:00 as 00:00
    return intervals

def task_input_form():
    """Sidebar form to add a new task."""
    with st.sidebar.expander("Add Task", expanded=False):
        if "task_start_time" not in st.session_state:
            st.session_state["task_start_time"] = datetime.now().time()
        if "task_end_time" not in st.session_state:
            st.session_state["task_end_time"] = (datetime.now() + timedelta(hours=1)).time()

        # Task form inputs
        TaskName = st.text_input("Task Name", "")
        Day = st.selectbox("Day of the Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        # StartTime = st.time_input("Start Time", value=st.session_state["task_start_time"])
        # EndTime = st.time_input("End Time", value=st.session_state["task_end_time"])
        intervals = generate_time_intervals()
        StartTime = st.selectbox("Start Time", options=intervals, format_func=lambda t: t.strftime("%H:%M"))
        EndTime = st.selectbox("End Time", options=intervals, format_func=lambda t: t.strftime("%H:%M"))

        duration_hours = st.number_input("Duration Hours", min_value=0, max_value=23, value=1)
        duration_minutes = st.number_input("Duration Minutes", min_value=0, max_value=59, value=0)
        NursesRequired = st.number_input("Nurses Required", min_value=1, value=1)

        # Update session state
        st.session_state["task_start_time"] = StartTime
        st.session_state["task_end_time"] = EndTime

        # Add task button
        if st.button("Add Task"):
            if TaskName:
                duration_delta = timedelta(hours=duration_hours, minutes=duration_minutes)
                add_task_to_db(
                    TaskName,
                    Day,
                    f"{StartTime.hour}:{StartTime.minute}:00",
                    f"{EndTime.hour}:{EndTime.minute}:00",
                    str(duration_delta),
                    NursesRequired
                )
                st.success(f"Task '{TaskName}' added!")
            else:
                st.error("Task name cannot be empty!")


def shift_input_form():
    """Sidebar form to add a new shift."""
    with st.sidebar.expander("Add Shift", expanded=False):
        if "shift_start_time" not in st.session_state:
            st.session_state["shift_start_time"] = datetime.now().time()
        if "shift_end_time" not in st.session_state:
            st.session_state["shift_end_time"] = (datetime.now() + timedelta(hours=1)).time()
        if "break_start_time" not in st.session_state:
            st.session_state["break_start_time"] = (datetime.now() + timedelta(hours=2)).time()

        intervals = generate_time_intervals()
        # Shift_StartTime = st.time_input("Shift Start Time", value=st.session_state["shift_start_time"])
        # Shift_EndTime = st.time_input("Shift End Time", value=st.session_state["shift_end_time"])
        # BreakTime = st.time_input("Break Start Time", value=st.session_state["break_start_time"])
        Shift_StartTime = st.selectbox("Shift Start Time", options=intervals, format_func=lambda t: t.strftime("%H:%M"))
        Shift_EndTime = st.selectbox("Shift End Time", options=intervals, format_func=lambda t: t.strftime("%H:%M"))
        BreakTime = st.selectbox("Break Start Time", options=intervals, format_func=lambda t: t.strftime("%H:%M"))

        BreakDuration_hours = st.number_input("Break Duration Hours", min_value=0, max_value=23, value=0)
        BreakDuration_minutes = st.number_input("Break Duration Minutes", min_value=0, max_value=59, value=30)
        Weight = st.number_input("Shift Weight", min_value=0.0, value=1.0)

        Days = {
            day: st.checkbox(day, value=(day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]))
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        }
        Notes = st.text_area("Additional Notes", "")

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


def worker_input_form():
    """Sidebar form to add a new worker with day-of-week preferences."""
    with st.sidebar.expander("Add Worker", expanded=False):
        worker_name = st.text_input("Worker Name", "")
        
        # We'll store each day's preference as Start/End time
        # If you want, you can default them to some typical 24-hour window for availability
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        start_times = {}
        end_times = {}
        
        for day in days:
            start_times[day] = st.time_input(f"{day} Start", datetime.strptime("08:00:00", "%H:%M:%S").time())
            end_times[day]   = st.time_input(f"{day} End", datetime.strptime("17:00:00", "%H:%M:%S").time())

        if st.button("Add Worker"):
            if worker_name.strip() == "":
                st.error("Worker name cannot be empty!")
            else:
                add_worker_to_db(
                    worker_name,
                    # Monday
                    f"{start_times['Monday'].hour}:{start_times['Monday'].minute}:00",
                    f"{end_times['Monday'].hour}:{end_times['Monday'].minute}:00",
                    # Tuesday
                    f"{start_times['Tuesday'].hour}:{start_times['Tuesday'].minute}:00",
                    f"{end_times['Tuesday'].hour}:{end_times['Tuesday'].minute}:00",
                    # Wednesday
                    f"{start_times['Wednesday'].hour}:{start_times['Wednesday'].minute}:00",
                    f"{end_times['Wednesday'].hour}:{end_times['Wednesday'].minute}:00",
                    # Thursday
                    f"{start_times['Thursday'].hour}:{start_times['Thursday'].minute}:00",
                    f"{end_times['Thursday'].hour}:{end_times['Thursday'].minute}:00",
                    # Friday
                    f"{start_times['Friday'].hour}:{start_times['Friday'].minute}:00",
                    f"{end_times['Friday'].hour}:{end_times['Friday'].minute}:00",
                    # Saturday
                    f"{start_times['Saturday'].hour}:{start_times['Saturday'].minute}:00",
                    f"{end_times['Saturday'].hour}:{end_times['Saturday'].minute}:00",
                    # Sunday
                    f"{start_times['Sunday'].hour}:{start_times['Sunday'].minute}:00",
                    f"{end_times['Sunday'].hour}:{end_times['Sunday'].minute}:00",
                )
                st.success(f"Worker '{worker_name}' added!")


def generate_and_fill_data_form():
    """Sidebar form to generate and fill random data."""
    with st.sidebar.expander("Generate Random Data", expanded=False):
        st.write("Generate random tasks and shifts to populate the database.")

        num_tasks = st.number_input("Number of Tasks", min_value=1, value=10, step=1)
        num_shifts = st.number_input("Number of Shifts", min_value=1, value=5, step=1)
        num_workers = st.number_input("Number of Workers", min_value=1, value=5, step=1)

        if st.button("Generate Data"):
            generate_and_fill_data(
                num_tasks=int(num_tasks),
                num_shifts=int(num_shifts),
                num_workers=int(num_workers)
            )
            st.success(f"Generated {num_tasks} tasks, {num_shifts} shifts, and {num_workers} workers successfully!")


def generate_and_fill_data(num_tasks=10, num_shifts=5, num_workers=5):
    """Generate random tasks, shifts, and workers and populate the database."""
    init_db()

    # Random tasks
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for _ in range(num_tasks):
        task_name = f"Task_{random.randint(1, 100)}"
        day = random.choice(days_of_week)
        start_time = datetime.now() + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
        duration = timedelta(hours=random.randint(0, 2), minutes=random.randint(0, 59))
        end_time = start_time + duration
        nurses_required = random.randint(1, 5)
        add_task_to_db(
            task_name,
            day,
            start_time.strftime("%H:%M:%S"),
            end_time.strftime("%H:%M:%S"),
            str(duration),
            nurses_required
        )

    # Random shifts
    for _ in range(num_shifts):
        start_time = datetime.now() + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
        duration = timedelta(hours=random.randint(1, 8))
        end_time = start_time + duration
        break_time = start_time + timedelta(hours=random.randint(1, int(duration.total_seconds() // 3600)))
        break_duration = timedelta(minutes=random.randint(15, 60))
        weight = random.uniform(0.5, 2.0)
        days = {day: random.choice([0, 1]) for day in days_of_week}

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

    # Random workers
    for _ in range(num_workers):
        wname = f"Worker_{random.randint(1, 100)}"
        # For each day, pick a random 8-hour preference window
        day_prefs = []
        for _day in days_of_week:
            start_h = random.randint(0, 8)  # earliest 0, latest 8
            end_h = start_h + random.randint(6, 10)  # random length between 6 and 10 hours
            day_prefs.append((start_h, end_h))

        add_worker_to_db(
            wname,
            # Monday
            f"{day_prefs[0][0]}:00:00", f"{day_prefs[0][1]}:00:00",
            # Tuesday
            f"{day_prefs[1][0]}:00:00", f"{day_prefs[1][1]}:00:00",
            # Wednesday
            f"{day_prefs[2][0]}:00:00", f"{day_prefs[2][1]}:00:00",
            # Thursday
            f"{day_prefs[3][0]}:00:00", f"{day_prefs[3][1]}:00:00",
            # Friday
            f"{day_prefs[4][0]}:00:00", f"{day_prefs[4][1]}:00:00",
            # Saturday
            f"{day_prefs[5][0]}:00:00", f"{day_prefs[5][1]}:00:00",
            # Sunday
            f"{day_prefs[6][0]}:00:00", f"{day_prefs[6][1]}:00:00",
        )


# ------------------------------------------------------------------
#                        Example Data Inserts
# ------------------------------------------------------------------
def insert():
    """
    Insert a small example data set into Tasks and Shifts.
    (For demonstration)
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO TasksTable1 (
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
    c.execute('''
        INSERT INTO ShiftsTable3 (
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


def insert2():
    """
    Another example data set.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO TasksTable1 (
            TaskName,
            Day,
            StartTime,
            EndTime,
            Duration,
            NursesRequired
        )
        VALUES
        ('Physical Therapy', 'Thursday', '07:00:00', '08:00:00', 45, 2),
        ('Vital Signs Monitoring', 'Friday', '06:00:00', '06:30:00', 30, 5),
        ('Vital Signs Monitoring', 'Wednesday', '05:30:00', '07:00:00', 60, 4),
        ('Medication Administration', 'Monday', '04:00:00', '05:30:00', 45, 1),
        ('Dressing Change', 'Saturday', '08:00:00', '10:00:00', 60, 4),
        ('Wound Care', 'Sunday', '12:30:00', '13:00:00', 15, 3),
        ('Vital Signs Monitoring', 'Thursday', '12:00:00', '13:00:00', 30, 5),
        ('Physical Therapy', 'Wednesday', '20:30:00', '23:30:00', 45, 2),
        ('Vital Signs Monitoring', 'Sunday', '21:30:00', '23:00:00', 30, 1),
        ('Physical Therapy', 'Saturday', '18:00:00', '19:00:00', 30, 5),
        ('Wound Care', 'Saturday', '00:00:00', '02:00:00', 60, 5),
        ('Vital Signs Monitoring', 'Tuesday', '19:30:00', '22:00:00', 30, 4),
        ('Wound Care', 'Monday', '19:00:00', '22:00:00', 15, 3),
        ('Medication Administration', 'Sunday', '11:00:00', '13:00:00', 60, 4),
        ('Physical Therapy', 'Thursday', '13:30:00', '16:30:00', 30, 1),
        ('Wound Care', 'Wednesday', '08:30:00', '10:00:00', 15, 2),
        ('Medication Administration', 'Tuesday', '17:00:00', '19:00:00', 60, 2),
        ('Medication Administration', 'Saturday', '19:30:00', '22:30:00', 30, 4),
        ('Dressing Change', 'Sunday', '15:30:00', '18:30:00', 15, 4),
        ('Vital Signs Monitoring', 'Tuesday', '04:30:00', '06:30:00', 60, 1),
        ('Wound Care', 'Wednesday', '22:00:00', '01:00:00', 30, 4),
        ('Physical Therapy', 'Tuesday', '17:00:00', '18:00:00', 45, 5),
        ('Dressing Change', 'Friday', '20:00:00', '21:30:00', 45, 3),
        ('Physical Therapy', 'Thursday', '02:00:00', '04:00:00', 60, 5),
        ('Dressing Change', 'Saturday', '22:00:00', '22:30:00', 30, 5),
        ('Wound Care', 'Friday', '09:30:00', '11:00:00', 15, 3),
        ('Vital Signs Monitoring', 'Saturday', '00:00:00', '03:00:00', 45, 3),
        ('Medication Administration', 'Monday', '02:30:00', '03:30:00', 30, 4),
        ('Vital Signs Monitoring', 'Monday', '12:30:00', '14:00:00', 30, 3),
        ('Dressing Change', 'Tuesday', '17:00:00', '19:30:00', 30, 5),
        ('Physical Therapy', 'Monday', '07:30:00', '08:00:00', 30, 4),
        ('Dressing Change', 'Wednesday', '17:00:00', '18:00:00', 15, 1),
        ('Physical Therapy', 'Thursday', '16:30:00', '17:00:00', 15, 2),
        ('Wound Care', 'Friday', '00:00:00', '00:30:00', 15, 5),
        ('Dressing Change', 'Friday', '18:30:00', '19:30:00', 45, 4),
        ('Wound Care', 'Sunday', '20:30:00', '23:00:00', 45, 2),
        ('Physical Therapy', 'Saturday', '09:00:00', '11:30:00', 60, 3),
        ('Vital Signs Monitoring', 'Thursday', '14:00:00', '15:00:00', 30, 4),
        ('Physical Therapy', 'Sunday', '13:00:00', '14:30:00', 15, 2),
        ('Dressing Change', 'Monday', '07:00:00', '09:00:00', 30, 3),
        ('Dressing Change', 'Sunday', '09:30:00', '10:00:00', 15, 2),
        ('Vital Signs Monitoring', 'Monday', '12:30:00', '14:30:00', 15, 3),
        ('Wound Care', 'Sunday', '21:00:00', '23:30:00', 15, 1),
        ('Physical Therapy', 'Monday', '21:30:00', '22:30:00', 15, 5),
        ('Medication Administration', 'Sunday', '15:00:00', '17:00:00', 45, 5),
        ('Vital Signs Monitoring', 'Tuesday', '20:00:00', '21:30:00', 45, 2),
        ('Wound Care', 'Monday', '06:30:00', '07:30:00', 15, 5),
        ('Physical Therapy', 'Wednesday', '21:30:00', '23:00:00', 30, 1),
        ('Physical Therapy', 'Friday', '17:30:00', '18:30:00', 60, 1),
        ('Physical Therapy', 'Thursday', '16:00:00', '18:00:00', 30, 5),
        ('Medication Administration', 'Thursday', '00:30:00', '02:00:00', 45, 2),
        ('Vital Signs Monitoring', 'Sunday', '01:00:00', '02:00:00', 60, 2),
        ('Medication Administration', 'Saturday', '14:00:00', '17:00:00', 45, 4),
        ('Physical Therapy', 'Friday', '17:00:00', '20:00:00', 45, 4),
        ('Physical Therapy', 'Sunday', '19:30:00', '20:30:00', 30, 4),
        ('Wound Care', 'Thursday', '01:00:00', '04:00:00', 60, 4),
        ('Wound Care', 'Saturday', '03:00:00', '05:00:00', 30, 5),
        ('Vital Signs Monitoring', 'Tuesday', '08:30:00', '09:30:00', 45, 3),
        ('Wound Care', 'Friday', '15:30:00', '16:00:00', 30, 2),
        ('Physical Therapy', 'Wednesday', '17:00:00', '19:00:00', 30, 3),
        ('Wound Care', 'Thursday', '06:30:00', '09:00:00', 60, 4),
        ('Medication Administration', 'Tuesday', '13:00:00', '15:30:00', 60, 1),
        ('Physical Therapy', 'Friday', '10:30:00', '13:30:00', 60, 5),
        ('Dressing Change', 'Tuesday', '06:00:00', '06:30:00', 15, 3),
        ('Physical Therapy', 'Sunday', '11:00:00', '14:00:00', 45, 2),
        ('Physical Therapy', 'Friday', '12:00:00', '13:30:00', 45, 2),
        ('Vital Signs Monitoring', 'Tuesday', '07:30:00', '10:00:00', 60, 1),
        ('Dressing Change', 'Tuesday', '19:30:00', '20:30:00', 45, 4),
        ('Wound Care', 'Thursday', '17:00:00', '17:30:00', 30, 3),
        ('Dressing Change', 'Sunday', '04:00:00', '06:30:00', 45, 2),
        ('Medication Administration', 'Thursday', '21:00:00', '23:00:00', 60, 3),
        ('Medication Administration', 'Monday', '04:30:00', '07:30:00', 30, 4),
        ('Physical Therapy', 'Friday', '21:00:00', '22:30:00', 45, 3),
        ('Vital Signs Monitoring', 'Wednesday', '13:00:00', '15:00:00', 30, 4),
        ('Wound Care', 'Saturday', '22:30:00', '01:00:00', 45, 1),
        ('Physical Therapy', 'Tuesday', '08:00:00', '09:00:00', 45, 3),
        ('Medication Administration', 'Sunday', '21:30:00', '00:30:00', 15, 3),
        ('Physical Therapy', 'Sunday', '12:00:00', '14:30:00', 60, 3),
        ('Physical Therapy', 'Sunday', '01:00:00', '03:00:00', 60, 3),
        ('Medication Administration', 'Saturday', '13:30:00', '14:30:00', 15, 3),
        ('Medication Administration', 'Tuesday', '18:00:00', '19:00:00', 15, 2),
        ('Physical Therapy', 'Wednesday', '15:00:00', '15:30:00', 30, 2),
        ('Wound Care', 'Sunday', '22:30:00', '01:30:00', 30, 4),
        ('Physical Therapy', 'Friday', '03:30:00', '04:30:00', 15, 4),
        ('Physical Therapy', 'Wednesday', '03:30:00', '04:30:00', 30, 5),
        ('Vital Signs Monitoring', 'Friday', '06:30:00', '07:30:00', 15, 3),
        ('Wound Care', 'Monday', '09:00:00', '10:00:00', 45, 2),
        ('Dressing Change', 'Thursday', '12:30:00', '13:00:00', 30, 2),
        ('Dressing Change', 'Friday', '09:30:00', '11:30:00', 30, 5),
        ('Wound Care', 'Wednesday', '20:30:00', '22:30:00', 60, 3),
        ('Vital Signs Monitoring', 'Saturday', '08:30:00', '09:30:00', 15, 4),
        ('Dressing Change', 'Sunday', '20:00:00', '23:00:00', 30, 1),
        ('Medication Administration', 'Thursday', '08:30:00', '11:00:00', 60, 2),
        ('Vital Signs Monitoring', 'Thursday', '22:30:00', '23:30:00', 30, 3),
        ('Physical Therapy', 'Tuesday', '21:30:00', '23:30:00', 60, 3),
        ('Dressing Change', 'Wednesday', '04:30:00', '05:00:00', 30, 5),
        ('Physical Therapy', 'Thursday', '15:30:00', '17:00:00', 60, 1),
        ('Wound Care', 'Saturday', '21:30:00', '22:30:00', 45, 3),
        ('Medication Administration', 'Saturday', '07:30:00', '09:30:00', 60, 3),
        ('Physical Therapy', 'Friday', '20:30:00', '21:00:00', 15, 1);
    ''')
    conn.commit()
    c.execute('''
        INSERT INTO ShiftsTable3 (
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
('06:15:00', '10:30:00', '08:30:00', '0:30:00', 4.25, 0, 1, 0, 0, 1, 0, 1, 1),
('14:15:00', '22:30:00', '16:45:00', '1:00:00', 8.25, 1, 1, 1, 0, 0, 1, 0, 1.5),
('20:00:00', '07:00:00', '22:00:00', '1:00:00', 11, 0, 1, 0, 1, 1, 0, 0, 1.5),
('04:00:00', '12:45:00', '06:00:00', '1:00:00', 8.75, 1, 0, 1, 0, 0, 0, 1, 2),
('12:30:00', '22:30:00', '14:30:00', '1:00:00', 10, 0, 0, 0, 0, 1, 0, 0, 1),
('02:00:00', '08:30:00', '04:15:00', '0:30:00', 6.5, 1, 1, 0, 1, 1, 1, 0, 2),
('20:00:00', '00:45:00', '22:00:00', '0:30:00', 4.75, 1, 0, 0, 1, 0, 1, 1, 1.5),
('15:30:00', '23:15:00', '17:00:00', '0:30:00', 7.75, 0, 1, 0, 1, 0, 0, 1, 1.5),
('19:15:00', '07:30:00', '21:30:00', '1:00:00', 12.25, 0, 0, 1, 1, 1, 1, 1, 1.5),
('18:00:00', '23:30:00', '20:15:00', '0:30:00', 5.5, 0, 0, 0, 1, 0, 0, 1, 1.5),
('05:15:00', '17:30:00', '07:30:00', '1:00:00', 12.25, 1, 1, 0, 0, 1, 1, 1, 2),
('08:30:00', '14:30:00', '10:45:00', '0:30:00', 6, 0, 1, 0, 1, 1, 0, 0, 1),
('19:30:00', '23:00:00', '21:00:00', '0:30:00', 3.5, 1, 0, 0, 0, 1, 0, 0, 1.5),
('15:15:00', '02:00:00', '17:30:00', '1:00:00', 10.75, 0, 1, 0, 1, 1, 1, 1, 1.5),
('05:30:00', '17:15:00', '07:30:00', '1:00:00', 11.75, 0, 1, 0, 1, 1, 1, 0, 2),
('18:00:00', '06:15:00', '20:00:00', '1:00:00', 12.25, 0, 1, 1, 1, 0, 1, 0, 1.5),
('04:45:00', '11:30:00', '06:00:00', '0:30:00', 6.75, 1, 0, 0, 1, 0, 1, 1, 2),
('23:30:00', '11:00:00', '01:45:00', '1:00:00', 11.5, 1, 0, 1, 1, 0, 0, 0, 2),
('23:45:00', '08:00:00', '01:15:00', '1:00:00', 8.25, 0, 1, 0, 1, 1, 0, 1, 2),
('03:30:00', '13:30:00', '05:30:00', '1:00:00', 10, 0, 1, 1, 0, 0, 0, 1, 2),
('14:15:00', '01:30:00', '16:00:00', '1:00:00', 11.25, 1, 1, 1, 0, 1, 1, 0, 1.5),
('21:00:00', '01:00:00', '23:15:00', '0:30:00', 4, 0, 1, 1, 0, 0, 1, 0, 1.5),
('10:30:00', '16:15:00', '12:15:00', '0:30:00', 5.75, 0, 1, 1, 1, 1, 0, 0, 1),
('20:45:00', '01:15:00', '22:30:00', '0:30:00', 4.5, 1, 1, 1, 1, 0, 0, 1, 1.5),
('02:15:00', '13:30:00', '04:30:00', '1:00:00', 11.25, 1, 0, 0, 1, 0, 0, 1, 2),
('08:15:00', '16:45:00', '10:45:00', '1:00:00', 8.5, 0, 0, 0, 0, 0, 0, 0, 1),
('11:15:00', '20:30:00', '13:00:00', '1:00:00', 9.25, 0, 0, 0, 0, 1, 0, 0, 1),
('22:00:00', '04:00:00', '00:30:00', '0:30:00', 6, 1, 1, 0, 0, 1, 1, 0, 2),
('22:00:00', '10:00:00', '00:00:00', '1:00:00', 12, 1, 1, 0, 0, 1, 0, 0, 2),
('09:30:00', '16:45:00', '11:00:00', '0:30:00', 7.25, 0, 0, 0, 0, 1, 1, 1, 1),
('09:15:00', '20:15:00', '11:30:00', '1:00:00', 11, 1, 1, 1, 1, 0, 0, 1, 1),
('04:30:00', '12:45:00', '06:30:00', '1:00:00', 8.25, 0, 1, 1, 1, 1, 0, 1, 2),
('18:30:00', '03:30:00', '20:00:00', '1:00:00', 9, 1, 1, 1, 0, 1, 1, 0, 1.5),
('16:30:00', '04:00:00', '18:45:00', '1:00:00', 11.5, 0, 0, 0, 1, 1, 0, 1, 1.5),
('17:30:00', '22:00:00', '19:30:00', '0:30:00', 4.5, 0, 1, 0, 1, 0, 0, 1, 1.5),
('19:00:00', '05:45:00', '21:00:00', '1:00:00', 10.75, 0, 1, 0, 1, 1, 0, 1, 1.5),
('21:00:00', '07:00:00', '23:00:00', '1:00:00', 10, 1, 0, 1, 1, 0, 1, 0, 1.5),
('23:45:00', '09:15:00', '01:15:00', '1:00:00', 9.5, 1, 0, 1, 0, 0, 1, 1, 2),
('21:45:00', '04:45:00', '23:15:00', '0:30:00', 7, 1, 1, 1, 0, 0, 0, 1, 1.5),
('00:30:00', '09:45:00', '02:00:00', '1:00:00', 9.25, 0, 1, 0, 1, 0, 0, 0, 2),
('23:45:00', '09:30:00', '01:45:00', '1:00:00', 9.75, 0, 1, 1, 0, 1, 0, 1, 2),
('22:15:00', '07:45:00', '00:45:00', '1:00:00', 9.5, 0, 1, 0, 1, 1, 1, 1, 2),
('01:15:00', '06:00:00', '03:00:00', '0:30:00', 4.75, 1, 0, 0, 1, 0, 0, 0, 2),
('17:15:00', '01:30:00', '19:15:00', '1:00:00', 8.25, 0, 1, 1, 1, 1, 0, 1, 1.5),
('15:00:00', '01:30:00', '17:00:00', '1:00:00', 10.5, 0, 0, 0, 0, 0, 1, 1, 1.5),
('23:45:00', '03:00:00', '01:30:00', '0:30:00', 3.25, 0, 1, 1, 0, 0, 1, 1, 2),
('22:45:00', '05:15:00', '00:00:00', '0:30:00', 6.5, 0, 0, 1, 1, 0, 1, 0, 2),
('22:15:00', '03:15:00', '00:30:00', '0:30:00', 5, 0, 0, 0, 1, 1, 1, 1, 2),
('17:45:00', '03:30:00', '19:15:00', '1:00:00', 9.75, 1, 0, 1, 0, 1, 0, 1, 1.5),
('04:15:00', '16:45:00', '06:30:00', '1:00:00', 12.5, 1, 0, 0, 1, 1, 0, 0, 2),
('17:00:00', '03:30:00', '19:00:00', '1:00:00', 10.5, 1, 0, 1, 1, 1, 0, 0, 1.5),
('06:45:00', '16:15:00', '08:45:00', '1:00:00', 9.5, 1, 0, 1, 1, 1, 0, 1, 1),
('21:00:00', '04:15:00', '23:00:00', '0:30:00', 7.25, 0, 1, 0, 1, 0, 1, 0, 1.5),
('11:15:00', '20:00:00', '13:15:00', '1:00:00', 8.75, 1, 1, 0, 0, 0, 1, 1, 1),
('22:00:00', '08:30:00', '00:00:00', '1:00:00', 10.5, 1, 1, 1, 0, 1, 0, 1, 2),
('21:15:00', '01:15:00', '23:30:00', '0:30:00', 4, 1, 1, 1, 0, 0, 0, 0, 1.5),
('02:00:00', '09:45:00', '04:00:00', '0:30:00', 7.75, 0, 1, 1, 1, 1, 0, 0, 2),
('08:30:00', '18:30:00', '10:45:00', '1:00:00', 10, 0, 0, 1, 1, 1, 1, 1, 1),
('22:45:00', '05:30:00', '00:15:00', '0:30:00', 6.75, 1, 1, 1, 1, 0, 0, 1, 2),
('23:30:00', '03:45:00', '01:45:00', '0:30:00', 4.25, 1, 0, 1, 0, 0, 0, 0, 2),
('15:15:00', '02:30:00', '17:15:00', '1:00:00', 11.25, 0, 0, 0, 0, 1, 0, 0, 1.5),
('20:45:00', '05:00:00', '22:00:00', '1:00:00', 8.25, 1, 0, 0, 0, 1, 0, 1, 1.5),
('19:00:00', '04:30:00', '21:45:00', '1:00:00', 9.5, 1, 1, 1, 1, 1, 1, 1, 1.5),
('10:30:00', '16:45:00', '12:45:00', '0:30:00', 6.25, 1, 1, 1, 1, 1, 0, 0, 1),
('20:45:00', '03:30:00', '22:00:00', '0:30:00', 6.75, 1, 0, 0, 0, 0, 0, 1, 1.5),
('01:45:00', '10:45:00', '03:45:00', '1:00:00', 9, 1, 1, 1, 1, 1, 1, 0, 2),
('01:30:00', '13:30:00', '03:45:00', '1:00:00', 12, 0, 0, 0, 1, 1, 0, 1, 2),
('19:45:00', '01:15:00', '21:30:00', '0:30:00', 5.5, 0, 0, 1, 0, 1, 0, 1, 1.5),
('13:45:00', '01:15:00', '15:00:00', '1:00:00', 11.5, 0, 0, 1, 0, 1, 1, 1, 1),
('19:45:00', '06:30:00', '21:00:00', '1:00:00', 10.75, 1, 0, 0, 1, 0, 1, 1, 1.5),
('14:15:00', '19:00:00', '16:00:00', '0:30:00', 4.75, 1, 1, 0, 1, 1, 0, 0, 1.5),
('10:30:00', '22:15:00', '12:15:00', '1:00:00', 11.75, 1, 0, 1, 0, 1, 1, 0, 1),
('21:45:00', '05:30:00', '23:00:00', '0:30:00', 7.75, 1, 0, 1, 1, 0, 0, 0, 1.5),
('20:45:00', '01:00:00', '22:15:00', '0:30:00', 4.25, 1, 1, 1, 0, 0, 1, 1, 1.5),
('14:00:00', '22:00:00', '16:30:00', '0:30:00', 8, 0, 0, 1, 0, 0, 0, 0, 1.5),
('17:30:00', '21:45:00', '19:30:00', '0:30:00', 4.25, 0, 1, 0, 1, 0, 0, 0, 1.5),
('20:30:00', '08:00:00', '22:45:00', '1:00:00', 11.5, 0, 0, 1, 0, 0, 1, 1, 1.5),
('15:00:00', '01:30:00', '17:00:00', '1:00:00', 10.5, 1, 0, 0, 0, 0, 1, 0, 1.5),
('19:45:00', '02:15:00', '21:30:00', '0:30:00', 6.5, 0, 0, 0, 1, 1, 0, 1, 1.5),
('03:00:00', '13:15:00', '05:30:00', '1:00:00', 10.25, 1, 0, 1, 0, 1, 0, 1, 2),
('03:15:00', '13:45:00', '05:15:00', '1:00:00', 10.5, 0, 0, 1, 0, 1, 0, 1, 2),
('03:00:00', '08:45:00', '05:30:00', '0:30:00', 5.75, 0, 0, 1, 0, 0, 1, 0, 2),
('08:15:00', '16:15:00', '10:45:00', '0:30:00', 8, 0, 0, 1, 0, 0, 0, 1, 1),
('04:45:00', '13:15:00', '06:00:00', '1:00:00', 8.5, 1, 1, 1, 1, 0, 0, 1, 2),
('13:15:00', '22:00:00', '15:15:00', '1:00:00', 8.75, 1, 1, 1, 1, 1, 1, 1, 1),
('11:15:00', '18:30:00', '13:00:00', '0:30:00', 7.25, 0, 1, 1, 0, 1, 0, 0, 1),
('21:00:00', '04:15:00', '23:00:00', '0:30:00', 7.25, 1, 1, 0, 0, 1, 0, 0, 1.5),
('00:00:00', '10:45:00', '02:15:00', '1:00:00', 10.75, 0, 0, 1, 1, 1, 1, 1, 2),
('09:15:00', '20:00:00', '11:00:00', '1:00:00', 10.75, 1, 0, 1, 1, 0, 0, 1, 1),
('12:30:00', '17:15:00', '14:30:00', '0:30:00', 4.75, 0, 0, 1, 0, 0, 0, 0, 1),
('05:15:00', '11:45:00', '07:45:00', '0:30:00', 6.5, 0, 1, 0, 1, 1, 1, 1, 2),
('10:00:00', '15:45:00', '12:00:00', '0:30:00', 5.75, 1, 1, 0, 1, 1, 1, 1, 1),
('08:45:00', '20:30:00', '10:45:00', '1:00:00', 11.75, 0, 1, 0, 0, 1, 0, 1, 1),
('01:45:00', '05:15:00', '03:15:00', '0:30:00', 3.5, 1, 0, 1, 0, 1, 1, 0, 2),
('10:15:00', '15:00:00', '12:15:00', '0:30:00', 4.75, 0, 1, 0, 1, 1, 1, 0, 1),
('21:30:00', '09:00:00', '23:45:00', '1:00:00', 11.5, 1, 0, 1, 0, 0, 0, 1, 1.5),
('13:45:00', '21:00:00', '15:45:00', '0:30:00', 7.25, 1, 0, 1, 0, 1, 1, 1, 1),
('18:00:00', '23:30:00', '20:00:00', '0:30:00', 5.5, 1, 1, 0, 0, 1, 0, 1, 1.5),
('22:15:00', '03:45:00', '00:15:00', '0:30:00', 5.5, 1, 0, 1, 1, 0, 0, 1, 2),
( '11:30:00', '22:45:00', '13:30:00', '1:00:00', 11.25, 1, 1, 0, 1, 0, 0, 1, 1);
    ''')
    conn.commit()
    conn.close()


# ------------------------------------------------------------------
#                     First Optimizer: Tasks-Shifts
# ------------------------------------------------------------------
def optimize_tasks_with_gurobi():
    """
    Assign tasks to shifts, and determine how many workers are needed per shift.
    This is the existing optimization for tasks.
    """
    tasks_df = get_all("Tasks")
    shifts_df = get_all("ShiftsTable3")

    if tasks_df.empty or shifts_df.empty:
        st.error("Tasks or shifts data is missing. Add data and try again.")
        return

    # Convert times
    tasks_df["StartTime"] = pd.to_datetime(tasks_df["StartTime"], format="%H:%M:%S").dt.time
    tasks_df["EndTime"] = pd.to_datetime(tasks_df["EndTime"], format="%H:%M:%S").dt.time
    shifts_df["StartTime"] = pd.to_datetime(shifts_df["StartTime"], format="%H:%M:%S").dt.time
    shifts_df["EndTime"] = pd.to_datetime(shifts_df["EndTime"], format="%H:%M:%S").dt.time

    # Create Gurobi Model
    model = Model("Task_Assignment")

    # Decision variables
    task_shift_vars = {}
    shift_worker_vars = {}

    for task_id, task in tasks_df.iterrows():
        for shift_id, shift in shifts_df.iterrows():
            # Check if shift can cover the task (matching day and time range)
            if (
                shift[task["Day"]] == 1 and
                shift["StartTime"] <= task["StartTime"] and
                shift["EndTime"] >= task["EndTime"]
            ):
                var_name = f"Task_{task_id}_Shift_{shift_id}"
                task_shift_vars[(task_id, shift_id)] = model.addVar(
                    vtype=GRB.BINARY, name=var_name
                )

    # Number of workers assigned to each shift
    for shift_id in shifts_df.index:
        shift_worker_vars[shift_id] = model.addVar(
            vtype=GRB.INTEGER, lb=0, name=f"Workers_Shift_{shift_id}"
        )

    # Objective: minimize total cost = sum(shift_workers * shift_weight)
    model.setObjective(
        quicksum(
            shift_worker_vars[shift_id] * shifts_df.loc[shift_id, "Weight"]
            for shift_id in shifts_df.index
        ),
        GRB.MINIMIZE
    )

    # Constraints
    # 1. Each task must be assigned to at least one shift that can cover it
    for task_id in tasks_df.index:
        feasible_shifts = [
            task_shift_vars[(task_id, s_id)]
            for s_id in shifts_df.index
            if (task_id, s_id) in task_shift_vars
        ]
        if feasible_shifts:
            model.addConstr(
                quicksum(feasible_shifts) >= 1,
                name=f"Task_{task_id}_Coverage"
            )

    # 2. Workers assigned to a shift must cover all tasks' nurse requirements
    for shift_id in shifts_df.index:
        model.addConstr(
            quicksum(
                task_shift_vars[(task_id, shift_id)] * tasks_df.loc[task_id, "NursesRequired"]
                for task_id in tasks_df.index if (task_id, shift_id) in task_shift_vars
            ) <= shift_worker_vars[shift_id],
            name=f"Shift_{shift_id}_Workers"
        )

    with st.spinner("Optimizing tasks and shifts. Please wait..."):
        model.optimize()

    # Collect results
    if model.status == GRB.OPTIMAL:
        results = []
        day_summary = {}

        for (task_id, shift_id), var in task_shift_vars.items():
            if var.x > 0.5:  # assigned
                task_day = tasks_df.loc[task_id, "Day"]
                workers_assigned = shift_worker_vars[shift_id].x

                # For reference, a simple “cost” can be computed, though the objective was total cost.
                # We'll distribute shift cost proportionally if multiple tasks are in the same shift:
                # This is not strictly necessary for the second optimization, but it’s illustrative.
                total_tasks_in_shift = sum(
                    task_shift_vars[(t_id, shift_id)].x > 0.5
                    for t_id in tasks_df.index if (t_id, shift_id) in task_shift_vars
                )
                if total_tasks_in_shift > 0 and workers_assigned > 0:
                    shift_cost_per_task = shifts_df.loc[shift_id, "Weight"] / total_tasks_in_shift
                    task_cost = shift_cost_per_task * (
                        tasks_df.loc[task_id, "NursesRequired"] / workers_assigned
                    )
                else:
                    task_cost = 0

                results.append({
                    "TaskID": tasks_df.loc[task_id, "id"],
                    "ShiftID": shifts_df.loc[shift_id, "id"],
                    "TaskName": tasks_df.loc[task_id, "TaskName"],
                    "TaskDay": task_day,
                    "TaskStart": tasks_df.loc[task_id, "StartTime"],
                    "TaskEnd": tasks_df.loc[task_id, "EndTime"],
                    "ShiftStart": shifts_df.loc[shift_id, "StartTime"],
                    "ShiftEnd": shifts_df.loc[shift_id, "EndTime"],
                    "ShiftNotes": shifts_df.loc[shift_id, "Notes"],
                    "WorkersNeededForShift": shift_worker_vars[shift_id].x,
                    "TaskCost": task_cost
                })

                # Update day summary
                if task_day not in day_summary:
                    day_summary[task_day] = {
                        "TotalCost": 0, "NumTasks": 0, "NumWorkers": 0
                    }
                day_summary[task_day]["TotalCost"] += task_cost
                day_summary[task_day]["NumTasks"] += 1
                day_summary[task_day]["NumWorkers"] += workers_assigned

        # Create DataFrames
        results_df = pd.DataFrame(results)

        if not results_df.empty:
            st.success("Task-shift optimization successful!")
            st.balloons()
            # update_needed_workers_for_each_day(results_df)
            day_summary_df = pd.DataFrame.from_dict(day_summary, orient="index").reset_index()

            day_summary_df.columns = ["Day", "TotalCost", "NumTasks", "NumWorkers"]
            st.write("**Optimal Task Assignments with Worker Counts**")
            st.dataframe(results_df,hide_index=True)

            st.download_button(
                label="Download Assignments as CSV",
                data=results_df.to_csv(index=False).encode("utf-8"),
                file_name="task_assignments_with_workers.csv",
                mime="text/csv"
            )

            st.write("**Daily Summary of Costs, Tasks, and Workers**")
            st.dataframe(day_summary_df,hide_index=True)

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
        model.computeIIS()
        for constr in model.getConstrs():
            if constr.IISConstr:
                st.write(f"Infeasible Constraint: {constr.constrName}")



def optimize_tasks_with_gurobi():
    """
    Assign tasks to (shift, day) pairs so that a single shift can have 
    different worker counts on different days.

    This version ensures that a Monday task won't force workers on Tuesday/Wednesday 
    if the shift is active multiple days.
    """

    # --- 1. Load Data ---
    tasks_df = get_all("TasksTable1")
    shifts_df = get_all("ShiftsTable3")

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

    # Column names in ShiftsTable3 for the days of the week
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
        st.write(f"task_id: {task_id}")
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
                    st.write(f"Variable created: {var_name}")

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
                shift_weight = shifts_df.loc[shift_id, "Weight"]
                if total_assigned_tasks > 0 and workers_assigned > 0:
                    cost_per_task = shift_weight / total_assigned_tasks
                    task_cost     = cost_per_task * (
                        tasks_df.loc[task_id, "NursesRequired"] / workers_assigned
                    )
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
    shifts_df = get_all("ShiftsTable3")
    workers_df = get_all("Workers")

    # The shift_worker_vars from the first optimization are not stored in DB,
    # but we do have the final integer result for each shift’s needed worker count
    # from the results CSV or from the model. Typically you'd store that in a table,
    # or re-run in memory. For this example, let's define a new column in ShiftsTable3
    # if you want (or we just pretend we have it). Instead, we will re-derive it from
    # the existing approach or just ask the user to enter "how many workers does each shift need?"

    # For demonstration, let's say the user manually enters a minimal coverage requirement
    # for each shift (like "1" or "2" or "3"). Alternatively, you can read the results
    # from a CSV or store them in a table. The code below checks for a column "NeededWorkers"
    # in ShiftsTable3. If missing, we fallback to a user-provided input.

    if "NeededWorkers" not in shifts_df.columns:
        st.info("**No 'NeededWorkers' column found in ShiftsTable3.**")
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
        st.success("Found 'NeededWorkers' column in ShiftsTable3. Using existing data.")

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


# ------------------------------------------------------------------
#                          Visualization
# ------------------------------------------------------------------
def display_tasks_and_shifts():
    """Display tasks and shifts as Gantt charts for the week."""
    st.header("Visualize Tasks and Shifts for the Week")

    tasks_df = get_all("TasksTable1")
    shifts_df = get_all("ShiftsTable3")

    if tasks_df.empty and shifts_df.empty:
        st.write("Tasks and shifts data is missing. Add data and try again.")
        return

    if not tasks_df.empty:
        st.write("**Tasks List**")
        st.dataframe(tasks_df,hide_index=True)
        st.download_button(
            label="Download Tasks as CSV",
            data=tasks_df.to_csv(index=False).encode("utf-8"),
            file_name="tasks.csv",
            mime="text/csv"
        )

    if not shifts_df.empty:
        st.write("**Shifts List**")
        st.dataframe(shifts_df,hide_index=True)
        st.download_button(
            label="Download Shifts as CSV",
            data=shifts_df.to_csv(index=False).encode("utf-8"),
            file_name="shifts.csv",
            mime="text/csv"
        )

    # If you want Gantt charts, we can do it with Plotly. 
    # (Same approach as in your existing code.)
    try:
        import plotly.express as px
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        full_day_range = ["2023-01-01 00:00:00", "2023-01-01 23:59:59"]

        # Prepare tasks DataFrame for Gantt
        if not tasks_df.empty:
            tasks_df["Start"] = pd.to_datetime("2023-01-01 " + tasks_df["StartTime"], format="%Y-%m-%d %H:%M:%S")
            tasks_df["End"]   = pd.to_datetime("2023-01-01 " + tasks_df["EndTime"],   format="%Y-%m-%d %H:%M:%S")
            tasks_df["Day"]   = pd.Categorical(tasks_df["Day"], categories=day_order, ordered=True)
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
                dtick=3600000,
                range=full_day_range
            )
            st.plotly_chart(fig_tasks)

        # Prepare shifts DataFrame for Gantt
        if not shifts_df.empty:
            shifts_df["Start"] = pd.to_datetime("2023-01-01 " + shifts_df["StartTime"], format="%Y-%m-%d %H:%M:%S")
            shifts_df["End"]   = pd.to_datetime("2023-01-01 " + shifts_df["EndTime"],   format="%Y-%m-%d %H:%M:%S")

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
                dtick=3600000,
                range=full_day_range
            )
            st.plotly_chart(fig_shifts)

    except Exception as e:
        st.warning(f"Plotly is required for Gantt charts: {e}")


# ------------------------------------------------------------------
#                            Main App
# ------------------------------------------------------------------
def main():
    init_db()
    st.title("Nursing ward planning")

    st.header("Tools")

    # Input forms
    task_input_form()
    shift_input_form()
    # worker_input_form()

    # with st.sidebar:
    #     st.markdown("---") 
    # generate_and_fill_data_form()

    with st.sidebar:
        st.markdown("---")  # Add a separator line
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Clear All Tasks"):
                clear_all("TasksTable1")
                st.success("All tasks have been cleared!")

        with col2:
            if st.button("Clear All Shifts"):
                clear_all("ShiftsTable3")
                st.success("All shifts have been cleared!")

        # if st.button("Clear All Workers"):
        #     clear_all("Workers")
        #     st.success("All workers have been cleared!")


    # Buttons for example data
    colA, colB = st.columns(2)
    with colA:
        if st.button("Data Example"):
            insert()
            st.success("Data Example 1 inserted!")
    with colB:
        if st.button("Data Example2"):
            insert2()
            st.success("Data Example 2 inserted!")

    # First optimization
    if st.button("Optimize Task Assignment"):
        optimize_tasks_with_gurobi()

    ## Second optimization: Assign workers to shifts
    # if st.button("Assign Workers to Shifts"):
    #     optimize_workers_for_shifts()


    # Visualization
    display_tasks_and_shifts()


if __name__ == "__main__":
    main()
