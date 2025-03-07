import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
from gurobipy import Model, GRB, quicksum
from datetime import time
import io  
import base64
import os
import datetime as dt
from gurobipy import GurobiError

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
        CREATE TABLE IF NOT EXISTS TasksTable3 (
            id INTEGER PRIMARY KEY,
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
    CREATE TABLE IF NOT EXISTS ShiftsTable6 (
        id INTEGER PRIMARY KEY,
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
    conn.commit()
    conn.close()

# -------------------------- DB Helpers ---------------------------
def add_task_to_db(TaskName, Day, StartTime, EndTime, Duration, NursesRequired):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO TasksTable3 (TaskName, Day, StartTime, EndTime, Duration, NursesRequired)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (TaskName, Day, StartTime, EndTime, Duration, NursesRequired))
    conn.commit()
    conn.close()

def add_shift_to_db(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO ShiftsTable6 (
            StartTime, EndTime, BreakTime, BreakDuration, Weight,
            Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


# ------------------------------------------------------------------
#                         Form Inputs
# ------------------------------------------------------------------

def generate_time_intervals():
    intervals = [time(hour=h, minute=m) for h in range(24) for m in range(0, 60, 15)]
    intervals.append(time(0, 0))  # Add 24:00 as 00:00
    return intervals

def task_input_form():
    """Sidebar form to add a new task."""
    with st.form("task_form", clear_on_submit=True):
        st.subheader("Add New Task")
        
        # Create two main columns for task details
        col1, col2 = st.columns(2)
        
        with col1:
            TaskName = st.text_input("Task Name*", key="task_name")
            
        with col2:
            NursesRequired = st.number_input("Nurses Required*", 
                                           min_value=1, value=1, step=1)
            
        Day = st.selectbox("Day of the Week*", 
                            ["Monday", "Tuesday", "Wednesday", "Thursday",
                            "Friday", "Saturday", "Sunday"])
        # Time inputs in their own columns
        time_col1, time_col2, time_col3 = st.columns(3)
        with time_col1:
            StartTime = st.time_input("Start Time*", value=time(9, 0))
        with time_col2:
            EndTime = st.time_input("End Time*", value=time(10, 0))
        with time_col3:
            duration = st.number_input("Duration*", 
                                     min_value=15, max_value=480, 
                                     value=60, step=15,help="Duration in minutes.")

        submitted = st.form_submit_button("➕ Add Task", use_container_width=True,type="primary")
            
        if submitted:
            if not TaskName:
                st.error("Task Name is required!")
            else:
                add_task_to_db(
                    TaskName,
                    Day,
                    StartTime.strftime("%H:%M:%S"),
                    EndTime.strftime("%H:%M:%S"),
                    str(timedelta(minutes=duration)),
                    NursesRequired
                )
                st.success("Task added successfully!")

def shift_input_form():
    """Sidebar form to add new shifts with proper day labels and weight sync."""
    with st.form("shift_form", clear_on_submit=True):
        st.subheader("Add New Shift")
        
        # --- Time Selection with 15-minute intervals ---
        intervals = generate_time_intervals()
        
        # Create columns for time inputs
        time_col1, time_col2 = st.columns(2)
        # Get index of 09:00 and 17:00 within intervals
        start_index = intervals.index(time(9, 0))
        end_index   = intervals.index(time(17, 0))
        with time_col1:
            Shift_StartTime = st.selectbox(
                "Shift Start*",
                intervals, 
                index=start_index,
                format_func=lambda t: t.strftime("%H:%M"),
                help="Select shift start time"
            )
        with time_col2:
            Shift_EndTime = st.selectbox(
                "Shift End*",
                intervals,
                index=end_index,
                format_func=lambda t: t.strftime("%H:%M"),
                help="Select shift end time"
            )

        # --- Break Configuration ---
        st.markdown("### Break Configuration")
        break_col1, break_col2 = st.columns(2)
        # Get index of 12:00 within intervals
        noon_index = intervals.index(time(12, 0))
        
        with break_col1:
            BreakTime = st.selectbox(
                "Break Start*",
                intervals,
                index=noon_index,  # <-- Default BreakTime at 12:00
                format_func=lambda t: t.strftime("%H:%M"),
                help="Select break start time"
            )
        with break_col2:
            break_durations = [15, 30, 45, 60, 75, 90, 105, 120]
            BreakDuration = st.selectbox("Break Duration*",
                                       options=break_durations,
                                       index=1,
                                       format_func=lambda x: f"{x} minutes")

        # --- Shift Weight with Synced Display ---
        # st.markdown("### Shift Preferences")
        
        # Weight = st.slider("Shift Weight ", 0.1, 1000.0, 1.0, 0.1,
        #                  help="Higher weight means more expensive to schedule")

        st.markdown("### Shift Preferences")
        Weight = st.number_input(
            "Shift Weight",
            min_value=0.1,
            max_value=100000000000000.0,
            value=1.0,
            step=0.1,
            help="Higher weight means more expensive to schedule"
        )
        





        
        # --- Days of Week Selection ---
        st.markdown("### Active Days ")
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        cols = st.columns(7)
        day_states = {}

        for i, col in enumerate(cols):
            with col:
                st.markdown(
                    f"""
                    <div style="
                        position: relative;
                        left: -0px;
                        top: 10px;
                        text-align: center;
                        width: 100%;
                    ">
                        {days[i]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div style='text-align: center; margin-bottom: -15px;'>"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                day_states[i] = st.toggle(
                    "",  # Empty label
                    key=f"day_{days[i]}" 
                )
        # --- Form Submission ---
        submitted = st.form_submit_button("➕ Add Shift", use_container_width=True)

        if submitted:
            errors = []
            
            # New validation: Check if at least one day is selected
            if not any(day_states.values()):
                errors.append("At least one day must be selected for the shift.")
            
            # Validate time sequence
            if Shift_StartTime >= Shift_EndTime:
                errors.append("Shift end time must be after start time")
                
            # Validate break time within shift
            if not (Shift_StartTime <= BreakTime < Shift_EndTime):
                errors.append("Break must occur during shift hours")
                
            # Validate break duration
            break_end = (datetime.combine(datetime.today(), BreakTime) 
                       + timedelta(minutes=BreakDuration)).time()
            if break_end > Shift_EndTime:
                errors.append("Break duration exceeds shift end time")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Convert days to database format
                active_days = [
                day_states[0],  # Monday
                day_states[1],  # Tuesday
                day_states[2],  # Wednesday
                day_states[3],  # Thursday
                day_states[4],  # Friday
                day_states[5],  # Saturday
                day_states[6]   # Sunday
                ]
                
                shift_data = (
                    Shift_StartTime.strftime("%H:%M:%S"),
                    Shift_EndTime.strftime("%H:%M:%S"),
                    BreakTime.strftime("%H:%M:%S"),
                    str(timedelta(minutes=BreakDuration)),
                    Weight,
                    *active_days
                )
                add_shift_to_db(shift_data)
                st.success("Shift added successfully!")

def task_template_download():
    """
    Provide a button to download a Task template *with example rows*,
    so users see the expected format and data types.
    """
    # Here, we include a couple of example tasks
    # showing how times and durations should be formatted.
    template_df = pd.DataFrame({
        "TaskName": ["Example Task", "Example Task"],
        "Day": ["Monday", "Tuesday"],                  # Must match "Monday"/"Tuesday"/... 
        "StartTime": ["07:30:00", "09:00:00"],         # "HH:MM:SS" format
        "EndTime": ["08:00:00", "09:30:00"],           # "HH:MM:SS" format
        "Duration": ["0:30:00", "0:30:00"],            # "HH:MM:SS" total duration
        "NursesRequired": [2, 1]                       # Integer
    })

    with st.container(border=False):
        
        # Create columns with large gap
        colA, colB = st.columns(2, gap="large")
        with colA:
            # --- CSV version ---
            csv_data = template_df.to_csv(index=False)
            st.download_button(
                label="Download Task Template (CSV)",
                data=csv_data.encode("utf-8"),
                file_name="task_template.csv",
                mime="text/csv",
                use_container_width=True
            )
        with colB:
            # --- Excel version ---
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                template_df.to_excel(writer, index=False, sheet_name='TaskTemplate')
            st.download_button(
                label="Download Task Template (Excel)",
                data=excel_buffer.getvalue(),
                file_name="task_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

def upload_tasks_excel():
    """
    Let the user upload a Task Excel file and insert into DB.
    """
    uploaded_file = st.file_uploader("Upload Task Excel", type=["xlsx", "xls", "csv"])
    if uploaded_file is not None:
        try:
            # Read either CSV or Excel automatically:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Validate that columns are present:
            required_cols = {"TaskName", "Day", "StartTime", "EndTime", "Duration", "NursesRequired"}
            missing = required_cols - set(df.columns)
            if missing:
                st.error(f"Your file is missing columns: {missing}")
                return
            
            # Insert each row into DB
            for _, row in df.iterrows():
                add_task_to_db(
                    row["TaskName"],
                    row["Day"],
                    str(row["StartTime"]),      # "HH:MM:SS" format
                    str(row["EndTime"]),        # "HH:MM:SS" format
                    str(row["Duration"]),       # e.g. "0:15:00"
                    int(row["NursesRequired"])
                )

            st.success("Tasks successfully uploaded and inserted into the database!")
        
        except Exception as e:
            st.error(f"Error reading file: {e}")

def shift_template_download():
    """
    Provide a button to download a Shifts template *with example rows*,
    so users see the expected format and data types.
    """
    # Include a couple of example shifts
    # showing how times and day-activation columns should be formatted.
    template_df = pd.DataFrame({
        "StartTime": ["07:00:00", "15:00:00"],      # "HH:MM:SS" format
        "EndTime": ["15:00:00", "23:00:00"],        # "HH:MM:SS" format
        "BreakTime": ["11:00:00", "19:00:00"],      # "HH:MM:SS"
        "BreakDuration": ["0:30:00", "1:00:00"],    # "HH:MM:SS"
        "Weight": [1200, 1400],                     # Float or int
        "Monday": [1, 1],    # 1 means shift is active that day, 0 means not active
        "Tuesday": [1, 1],
        "Wednesday": [1, 1],
        "Thursday": [1, 1],
        "Friday": [1, 1],
        "Saturday": [0, 1],
        "Sunday": [0, 1]
    })

    with st.container(border=False):
        
        # Create columns with large gap
        colA, colB = st.columns(2, gap="large")
        
        with colA:
            # --- CSV version ---
            csv_data = template_df.to_csv(index=False)
            st.download_button(
                label="Download Shift Template (CSV)",
                data=csv_data.encode("utf-8"),
                file_name="shift_template.csv",
                mime="text/csv",
                use_container_width=True  # Make button fill column width
            )
        
        with colB:
            # --- Excel version ---
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                template_df.to_excel(writer, index=False, sheet_name='ShiftTemplate')
            st.download_button(
                label="Download Shift Template (Excel)",
                data=excel_buffer.getvalue(),
                file_name="shift_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True  # Make button fill column width
            )

def upload_shifts_excel():
    """
    Let the user upload a Shifts Excel file (or CSV) to populate the DB.
    """
    uploaded_file = st.file_uploader("Upload Shifts File", type=["xlsx", "xls", "csv"])
    if uploaded_file is not None:
        try:
            # Read CSV or Excel automatically:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Validate that columns are present:
            required_cols = {
                "StartTime", "EndTime", "BreakTime", "BreakDuration", "Weight",
                "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
            }
            missing = required_cols - set(df.columns)
            if missing:
                st.error(f"Your file is missing columns: {missing}")
                return

            # Insert each row into DB
            for _, row in df.iterrows():
                shift_data = (
                    str(row["StartTime"]),      # e.g. "07:00:00"
                    str(row["EndTime"]),        # e.g. "15:00:00"
                    str(row["BreakTime"]),      # e.g. "11:00:00"
                    str(row["BreakDuration"]),  # e.g. "0:30:00"
                    float(row["Weight"]),
                    int(row["Monday"]),
                    int(row["Tuesday"]),
                    int(row["Wednesday"]),
                    int(row["Thursday"]),
                    int(row["Friday"]),
                    int(row["Saturday"]),
                    int(row["Sunday"])
                )
                add_shift_to_db(shift_data)

            st.success("Shifts successfully uploaded and inserted into the database!")
        
        except Exception as e:
            st.error(f"Error reading file: {e}")


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
        INSERT INTO TasksTable3 (
            TaskName,
            Day,
            StartTime,
            EndTime,
            Duration,
            NursesRequired
        )
        VALUES
            ('Dressing Change', 'Monday', '07:30:00', '07:45:00', '0:15:00', 1),
            ('Vital Signs Monitoring', 'Monday', '10:30:00', '11:00:00', '0:30:00', 2),
            ('Wound Care', 'Monday', '14:30:00', '15:15:00', '0:45:00', 3),
            ('Medication Administration', 'Monday', '22:00:00', '22:30:00', '0:30:00', 2),
            ('Physical Therapy', 'Tuesday', '08:00:00', '08:45:00','0:45:00', 2),
            ('Dressing Change', 'Tuesday', '13:30:00', '13:45:00', '0:15:00', 1),
            ('Vital Signs Monitoring', 'Tuesday', '16:00:00', '16:30:00', '0:15:00', 2),
            ('Medication Administration', 'Tuesday', '21:30:00', '22:00:00', '0:30:00', 2),
            ('Wound Care', 'Wednesday', '07:30:00', '08:15:00', '0:45:00', 3),
            ('Physical Therapy', 'Wednesday', '12:00:00', '12:45:00', '0:45:00', 2),
            ('Dressing Change', 'Wednesday', '18:00:00', '18:15:00', '0:15:00', 1),
            ('Vital Signs Monitoring', 'Thursday', '09:00:00', '09:30:00', '0:30:00', 2),
            ('Medication Administration', 'Thursday', '13:00:00', '13:30:00', '0:30:00', 2),
            ('Wound Care', 'Thursday', '17:30:00', '18:15:00', '0:45:00', 3),
            ('Dressing Change', 'Friday', '07:30:00', '07:45:00', '0:15:00', 1),
            ('Vital Signs Monitoring', 'Friday', '14:30:00', '15:00:00', '0:30:00', 2),
            ('Medication Administration', 'Friday', '21:30:00', '22:00:00', '0:30:00', 2),
            ('Wound Care', 'Saturday', '09:30:00', '10:15:00', '0:45:00', 3),
            ('Physical Therapy', 'Saturday', '14:00:00', '14:45:00', '0:45:00', 2),
            ('Vital Signs Monitoring', 'Saturday', '20:00:00', '20:30:00', '0:30:00', 2),
            ('Dressing Change', 'Sunday', '14:30:00', '14:45:00', '0:15:00', 1),
            ('Wound Care', 'Sunday', '20:00:00', '20:45:00', '0:15:00', 3);
    ''')
    conn.commit()
    c.execute('''
        INSERT INTO ShiftsTable6 (
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
            Sunday
        )
        VALUES
            ('07:00:00', '15:00:00', '11:00:00', '0:30:00', 1200, 1, 1, 1, 1, 1, 0, 0),
            ('15:00:00', '23:00:00', '19:00:00', '0:30:00', 1400, 1, 1, 1, 1, 1, 1, 1),
            ('23:00:00', '07:00:00', '03:00:00', '0:30:00', 1600, 1, 1, 1, 1, 1, 1, 1),
            ('08:00:00', '14:00:00', '12:00:00', '0:20:00', 1000, 1, 1, 1, 1, 1, 0, 0),
            ('14:00:00', '20:00:00', '17:00:00', '0:30:00', 1100, 1, 1, 1, 1, 1, 1, 1),
            ('20:00:00', '02:00:00', '23:00:00', '0:20:00', 1300, 0, 1, 1, 1, 1, 1, 1),
            ('09:00:00', '17:00:00', '13:00:00', '0:45:00', 1500, 1, 1, 0, 1, 1, 0, 0),
            ('06:00:00', '14:00:00', '10:00:00', '0:30:00', 1100, 1, 1, 1, 1, 1, 1, 0),
            ('14:00:00', '22:00:00', '18:00:00', '0:30:00', 1200, 1, 1, 1, 1, 1, 1, 1),
            ('10:00:00', '18:00:00', '13:30:00', '0:30:00', 1300, 1, 1, 1, 1, 1, 0, 0);
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
        INSERT INTO TasksTable3 (
            TaskName,
            Day,
            StartTime,
            EndTime,
            Duration,
            NursesRequired
        )
        VALUES
        ('Physical Therapy', 'Thursday', '07:00:00', '08:00:00', '0:45:00', 2),
        ('Vital Signs Monitoring', 'Friday', '06:00:00', '06:30:00', '0:30:00', 5),
        ('Vital Signs Monitoring', 'Wednesday', '05:30:00', '07:00:00', '1:00:00', 4),
        ('Medication Administration', 'Monday', '04:00:00', '05:30:00', '0:45:00', 1),
        ('Dressing Change', 'Saturday', '08:00:00', '10:00:00', '1:00:00', 4),
        ('Wound Care', 'Sunday', '12:30:00', '13:00:00', '0:15:00', 3),
        ('Vital Signs Monitoring', 'Thursday', '12:00:00', '13:00:00', '0:30:00', 5),
        ('Physical Therapy', 'Wednesday', '20:30:00', '23:30:00', '0:45:00', 2),
        ('Vital Signs Monitoring', 'Sunday', '21:30:00', '23:00:00', '0:30:00', 1),
        ('Physical Therapy', 'Saturday', '18:00:00', '19:00:00', '0:30:00', 5),
        ('Wound Care', 'Saturday', '00:00:00', '02:00:00', '1:00:00', 5),
        ('Vital Signs Monitoring', 'Tuesday', '19:30:00', '22:00:00', '0:30:00', 4),
        ('Wound Care', 'Monday', '19:00:00', '22:00:00', '0:15:00', 3),
        ('Medication Administration', 'Sunday', '11:00:00', '13:00:00', '1:00:00', 4),
        ('Physical Therapy', 'Thursday', '13:30:00', '16:30:00', '0:30:00', 1),
        ('Wound Care', 'Wednesday', '08:30:00', '10:00:00', '0:15:00', 2),
        ('Medication Administration', 'Tuesday', '17:00:00', '19:00:00', '1:00:00', 2),
        ('Medication Administration', 'Saturday', '19:30:00', '22:30:00', '0:30:00', 4),
        ('Dressing Change', 'Sunday', '15:30:00', '18:30:00', '0:15:00', 4),
        ('Vital Signs Monitoring', 'Tuesday', '04:30:00', '06:30:00', '1:00:00', 1),
        ('Wound Care', 'Wednesday', '22:00:00', '01:00:00', '0:30:00', 4),
        ('Physical Therapy', 'Tuesday', '17:00:00', '18:00:00', '0:45:00', 5),
        ('Dressing Change', 'Friday', '20:00:00', '21:30:00', '0:45:00', 3),
        ('Physical Therapy', 'Thursday', '02:00:00', '04:00:00', '1:00:00', 5),
        ('Dressing Change', 'Saturday', '22:00:00', '22:30:00', '0:30:00', 5),
        ('Wound Care', 'Friday', '09:30:00', '11:00:00', '0:15:00', 3),
        ('Vital Signs Monitoring', 'Saturday', '00:00:00', '03:00:00', '0:45:00', 3),
        ('Medication Administration', 'Monday', '02:30:00', '03:30:00', '0:30:00', 4),
        ('Vital Signs Monitoring', 'Monday', '12:30:00', '14:00:00', '0:30:00', 3),
        ('Dressing Change', 'Tuesday', '17:00:00', '19:30:00', '0:30:00', 5),
        ('Physical Therapy', 'Monday', '07:30:00', '08:00:00', '0:30:00', 4),
        ('Dressing Change', 'Wednesday', '17:00:00', '18:00:00', '0:15:00', 1),
        ('Physical Therapy', 'Thursday', '16:30:00', '17:00:00', '0:15:00', 2),
        ('Wound Care', 'Friday', '00:00:00', '00:30:00', '0:15:00', 5),
        ('Dressing Change', 'Friday', '18:30:00', '19:30:00', '0:45:00', 4),
        ('Wound Care', 'Sunday', '20:30:00', '23:00:00', '0:45:00', 2),
        ('Physical Therapy', 'Saturday', '09:00:00', '11:30:00', '1:00:00', 3),
        ('Vital Signs Monitoring', 'Thursday', '14:00:00', '15:00:00', '0:30:00', 4),
        ('Physical Therapy', 'Sunday', '13:00:00', '14:30:00', '0:15:00', 2),
        ('Dressing Change', 'Monday', '07:00:00', '09:00:00', '0:30:00', 3),
        ('Dressing Change', 'Sunday', '09:30:00', '10:00:00', '0:15:00', 2),
        ('Vital Signs Monitoring', 'Monday', '12:30:00', '14:30:00', '0:15:00', 3),
        ('Wound Care', 'Sunday', '21:00:00', '23:30:00', '0:15:00', 1),
        ('Physical Therapy', 'Monday', '21:30:00', '22:30:00', '0:15:00', 5),
        ('Medication Administration', 'Sunday', '15:00:00', '17:00:00', '0:45:00', 5),
        ('Vital Signs Monitoring', 'Tuesday', '20:00:00', '21:30:00', '0:45:00', 2),
        ('Wound Care', 'Monday', '06:30:00', '07:30:00', '0:15:00', 5),
        ('Physical Therapy', 'Wednesday', '21:30:00', '23:00:00', '0:30:00', 1),
        ('Physical Therapy', 'Friday', '17:30:00', '18:30:00', '1:00:00', 1),
        ('Physical Therapy', 'Thursday', '16:00:00', '18:00:00', '0:30:00', 5),
        ('Medication Administration', 'Thursday', '00:30:00', '02:00:00', '0:45:00', 2),
        ('Vital Signs Monitoring', 'Sunday', '01:00:00', '02:00:00', '1:00:00', 2),
        ('Medication Administration', 'Saturday', '14:00:00', '17:00:00', '0:45:00', 4),
        ('Physical Therapy', 'Friday', '17:00:00', '20:00:00', '0:45:00', 4),
        ('Physical Therapy', 'Sunday', '19:30:00', '20:30:00', '0:30:00', 4),
        ('Wound Care', 'Thursday', '01:00:00', '04:00:00', '1:00:00', 4),
        ('Wound Care', 'Saturday', '03:00:00', '05:00:00', '0:30:00', 5),
        ('Vital Signs Monitoring', 'Tuesday', '08:30:00', '09:30:00', '0:45:00', 3),
        ('Wound Care', 'Friday', '15:30:00', '16:00:00', '0:30:00', 2),
        ('Physical Therapy', 'Wednesday', '17:00:00', '19:00:00', '0:30:00', 3),
        ('Wound Care', 'Thursday', '06:30:00', '09:00:00', '1:00:00', 4),
        ('Medication Administration', 'Tuesday', '13:00:00', '15:30:00', '1:00:00', 1),
        ('Physical Therapy', 'Friday', '10:30:00', '13:30:00', '1:00:00', 5),
        ('Dressing Change', 'Tuesday', '06:00:00', '06:30:00', '0:15:00', 3),
        ('Physical Therapy', 'Sunday', '11:00:00', '14:00:00', '0:45:00', 2),
        ('Physical Therapy', 'Friday', '12:00:00', '13:30:00', '0:45:00', 2),
        ('Vital Signs Monitoring', 'Tuesday', '07:30:00', '10:00:00', '1:00:00', 1),
        ('Dressing Change', 'Tuesday', '19:30:00', '20:30:00', '0:45:00', 4),
        ('Wound Care', 'Thursday', '17:00:00', '17:30:00', '0:30:00', 3),
        ('Dressing Change', 'Sunday', '04:00:00', '06:30:00', '0:45:00', 2),
        ('Medication Administration', 'Thursday', '21:00:00', '23:00:00', '1:00:00', 3),
        ('Medication Administration', 'Monday', '04:30:00', '07:30:00', '0:30:00', 4),
        ('Physical Therapy', 'Friday', '21:00:00', '22:30:00', '0:45:00', 3),
        ('Vital Signs Monitoring', 'Wednesday', '13:00:00', '15:00:00', '0:30:00', 4),
        ('Wound Care', 'Saturday', '22:30:00', '01:00:00', '0:45:00', 1),
        ('Physical Therapy', 'Tuesday', '08:00:00', '09:00:00', '0:45:00', 3),
        ('Medication Administration', 'Sunday', '21:30:00', '00:30:00', '0:15:00', 3),
        ('Physical Therapy', 'Sunday', '12:00:00', '14:30:00', '1:00:00', 3),
        ('Physical Therapy', 'Sunday', '01:00:00', '03:00:00', '1:00:00', 3),
        ('Medication Administration', 'Saturday', '13:30:00', '14:30:00', '0:15:00', 3),
        ('Medication Administration', 'Tuesday', '18:00:00', '19:00:00', '0:15:00', 2),
        ('Physical Therapy', 'Wednesday', '15:00:00', '15:30:00', '0:30:00', 2),
        ('Wound Care', 'Sunday', '22:30:00', '01:30:00', '0:30:00', 4),
        ('Physical Therapy', 'Friday', '03:30:00', '04:30:00', '0:15:00', 4),
        ('Physical Therapy', 'Wednesday', '03:30:00', '04:30:00', '0:30:00', 5),
        ('Vital Signs Monitoring', 'Friday', '06:30:00', '07:30:00', '0:15:00', 3),
        ('Wound Care', 'Monday', '09:00:00', '10:00:00', '0:45:00', 2),
        ('Dressing Change', 'Thursday', '12:30:00', '13:00:00', '0:30:00', 2),
        ('Dressing Change', 'Friday', '09:30:00', '11:30:00', '0:30:00', 5),
        ('Wound Care', 'Wednesday', '20:30:00', '22:30:00', '1:00:00', 3),
        ('Vital Signs Monitoring', 'Saturday', '08:30:00', '09:30:00', '0:15:00', 4),
        ('Dressing Change', 'Sunday', '20:00:00', '23:00:00', '0:30:00', 1),
        ('Medication Administration', 'Thursday', '08:30:00', '11:00:00', '1:00:00', 2),
        ('Vital Signs Monitoring', 'Thursday', '22:30:00', '23:30:00', '0:30:00', 3),
        ('Physical Therapy', 'Tuesday', '21:30:00', '23:30:00', '1:00:00', 3),
        ('Dressing Change', 'Wednesday', '04:30:00', '05:00:00', '0:30:00', 5),
        ('Physical Therapy', 'Thursday', '15:30:00', '17:00:00', '1:00:00', 1),
        ('Wound Care', 'Saturday', '21:30:00', '22:30:00', '0:45:00', 3),
        ('Medication Administration', 'Saturday', '07:30:00', '09:30:00', '1:00:00', 3),
        ('Physical Therapy', 'Friday', '20:30:00', '21:00:00', '0:15:00', 1);

    ''')
    conn.commit()
    c.execute('''
        INSERT INTO ShiftsTable6 (
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
            Sunday
        )
        VALUES
('06:15:00', '10:30:00', '08:30:00', '0:30:00', 4.25, 0, 1, 0, 0, 1, 0, 1),
('14:15:00', '22:30:00', '16:45:00', '1:00:00', 8.25, 1, 1, 1, 0, 0, 1, 0),
('20:00:00', '07:00:00', '22:00:00', '1:00:00', 11, 0, 1, 0, 1, 1, 0, 0),
('04:00:00', '12:45:00', '06:00:00', '1:00:00', 8.75, 1, 0, 1, 0, 0, 0, 1),
('12:30:00', '22:30:00', '14:30:00', '1:00:00', 10, 0, 0, 0, 0, 1, 0, 0),
('02:00:00', '08:30:00', '04:15:00', '0:30:00', 6.5, 1, 1, 0, 1, 1, 1, 0),
('20:00:00', '00:45:00', '22:00:00', '0:30:00', 4.75, 1, 0, 0, 1, 0, 1, 1),
('15:30:00', '23:15:00', '17:00:00', '0:30:00', 7.75, 0, 1, 0, 1, 0, 0, 1),
('19:15:00', '07:30:00', '21:30:00', '1:00:00', 12.25, 0, 0, 1, 1, 1, 1, 1),
('18:00:00', '23:30:00', '20:15:00', '0:30:00', 5.5, 0, 0, 0, 1, 0, 0, 1),
('05:15:00', '17:30:00', '07:30:00', '1:00:00', 12.25, 1, 1, 0, 0, 1, 1, 1),
('08:30:00', '14:30:00', '10:45:00', '0:30:00', 6, 0, 1, 0, 1, 1, 0, 0),
('19:30:00', '23:00:00', '21:00:00', '0:30:00', 3.5, 1, 0, 0, 0, 1, 0, 0),
('15:15:00', '02:00:00', '17:30:00', '1:00:00', 10.75, 0, 1, 0, 1, 1, 1, 1),
('05:30:00', '17:15:00', '07:30:00', '1:00:00', 11.75, 0, 1, 0, 1, 1, 1, 0),
('18:00:00', '06:15:00', '20:00:00', '1:00:00', 12.25, 0, 1, 1, 1, 0, 1, 0),
('04:45:00', '11:30:00', '06:00:00', '0:30:00', 6.75, 1, 0, 0, 1, 0, 1, 1),
('23:30:00', '11:00:00', '01:45:00', '1:00:00', 11.5, 1, 0, 1, 1, 0, 0, 0),
('23:45:00', '08:00:00', '01:15:00', '1:00:00', 8.25, 0, 1, 0, 1, 1, 0, 1),
('03:30:00', '13:30:00', '05:30:00', '1:00:00', 10, 0, 1, 1, 0, 0, 0, 1),
('14:15:00', '01:30:00', '16:00:00', '1:00:00', 11.25, 1, 1, 1, 0, 1, 1, 0),
('21:00:00', '01:00:00', '23:15:00', '0:30:00', 4, 0, 1, 1, 0, 0, 1, 0),
('10:30:00', '16:15:00', '12:15:00', '0:30:00', 5.75, 0, 1, 1, 1, 1, 0, 0),
('20:45:00', '01:15:00', '22:30:00', '0:30:00', 4.5, 1, 1, 1, 1, 0, 0, 1),
('02:15:00', '13:30:00', '04:30:00', '1:00:00', 11.25, 1, 0, 0, 1, 0, 0, 1),
('08:15:00', '16:45:00', '10:45:00', '1:00:00', 8.5, 0, 0, 0, 0, 0, 0, 0),
('11:15:00', '20:30:00', '13:00:00', '1:00:00', 9.25, 0, 0, 0, 0, 1, 0, 0),
('22:00:00', '04:00:00', '00:30:00', '0:30:00', 6, 1, 1, 0, 0, 1, 1, 0),
('22:00:00', '10:00:00', '00:00:00', '1:00:00', 12, 1, 1, 0, 0, 1, 0, 0),
('09:30:00', '16:45:00', '11:00:00', '0:30:00', 7.25, 0, 0, 0, 0, 1, 1, 1),
('09:15:00', '20:15:00', '11:30:00', '1:00:00', 11, 1, 1, 1, 1, 0, 0, 1),
('04:30:00', '12:45:00', '06:30:00', '1:00:00', 8.25, 0, 1, 1, 1, 1, 0, 1),
('18:30:00', '03:30:00', '20:00:00', '1:00:00', 9, 1, 1, 1, 0, 1, 1, 0),
('16:30:00', '04:00:00', '18:45:00', '1:00:00', 11.5, 0, 0, 0, 1, 1, 0, 1),
('17:30:00', '22:00:00', '19:30:00', '0:30:00', 4.5, 0, 1, 0, 1, 0, 0, 1),
('19:00:00', '05:45:00', '21:00:00', '1:00:00', 10.75, 0, 1, 0, 1, 1, 0, 1),
('21:00:00', '07:00:00', '23:00:00', '1:00:00', 10, 1, 0, 1, 1, 0, 1, 0),
('23:45:00', '09:15:00', '01:15:00', '1:00:00', 9.5, 1, 0, 1, 0, 0, 1, 1),
('21:45:00', '04:45:00', '23:15:00', '0:30:00', 7, 1, 1, 1, 0, 0, 0, 1),
('00:30:00', '09:45:00', '02:00:00', '1:00:00', 9.25, 0, 1, 0, 1, 0, 0, 0),
('23:45:00', '09:30:00', '01:45:00', '1:00:00', 9.75, 0, 1, 1, 0, 1, 0, 1),
('22:15:00', '07:45:00', '00:45:00', '1:00:00', 9.5, 0, 1, 0, 1, 1, 1, 1),
('01:15:00', '06:00:00', '03:00:00', '0:30:00', 4.75, 1, 0, 0, 1, 0, 0, 0),
('17:15:00', '01:30:00', '19:15:00', '1:00:00', 8.25, 0, 1, 1, 1, 1, 0, 1),
('15:00:00', '01:30:00', '17:00:00', '1:00:00', 10.5, 0, 0, 0, 0, 0, 1, 1),
('23:45:00', '03:00:00', '01:30:00', '0:30:00', 3.25, 0, 1, 1, 0, 0, 1, 1),
('22:45:00', '05:15:00', '00:00:00', '0:30:00', 6.5, 0, 0, 1, 1, 0, 1, 0),
('22:15:00', '03:15:00', '00:30:00', '0:30:00', 5, 0, 0, 0, 1, 1, 1, 1),
('17:45:00', '03:30:00', '19:15:00', '1:00:00', 9.75, 1, 0, 1, 0, 1, 0, 1),
('04:15:00', '16:45:00', '06:30:00', '1:00:00', 12.5, 1, 0, 0, 1, 1, 0, 0),
('17:00:00', '03:30:00', '19:00:00', '1:00:00', 10.5, 1, 0, 1, 1, 1, 0, 0),
('06:45:00', '16:15:00', '08:45:00', '1:00:00', 9.5, 1, 0, 1, 1, 1, 0, 1),
('21:00:00', '04:15:00', '23:00:00', '0:30:00', 7.25, 0, 1, 0, 1, 0, 1, 0),
('11:15:00', '20:00:00', '13:15:00', '1:00:00', 8.75, 1, 1, 0, 0, 0, 1, 1),
('22:00:00', '08:30:00', '00:00:00', '1:00:00', 10.5, 1, 1, 1, 0, 1, 0, 1),
('21:15:00', '01:15:00', '23:30:00', '0:30:00', 4, 1, 1, 1, 0, 0, 0, 0),
('02:00:00', '09:45:00', '04:00:00', '0:30:00', 7.75, 0, 1, 1, 1, 1, 0, 0),
('08:30:00', '18:30:00', '10:45:00', '1:00:00', 10, 0, 0, 1, 1, 1, 1, 1),
('22:45:00', '05:30:00', '00:15:00', '0:30:00', 6.75, 1, 1, 1, 1, 0, 0, 1),
('23:30:00', '03:45:00', '01:45:00', '0:30:00', 4.25, 1, 0, 1, 0, 0, 0, 0),
('15:15:00', '02:30:00', '17:15:00', '1:00:00', 11.25, 0, 0, 0, 0, 1, 0, 0),
('20:45:00', '05:00:00', '22:00:00', '1:00:00', 8.25, 1, 0, 0, 0, 1, 0, 1),
('19:00:00', '04:30:00', '21:45:00', '1:00:00', 9.5, 1, 1, 1, 1, 1, 1, 1),
('10:30:00', '16:45:00', '12:45:00', '0:30:00', 6.25, 1, 1, 1, 1, 1, 0, 0),
('20:45:00', '03:30:00', '22:00:00', '0:30:00', 6.75, 1, 0, 0, 0, 0, 0, 1),
('01:45:00', '10:45:00', '03:45:00', '1:00:00', 9, 1, 1, 1, 1, 1, 1, 0),
('01:30:00', '13:30:00', '03:45:00', '1:00:00', 12, 0, 0, 0, 1, 1, 0, 1),
('19:45:00', '01:15:00', '21:30:00', '0:30:00', 5.5, 0, 0, 1, 0, 1, 0, 1),
('13:45:00', '01:15:00', '15:00:00', '1:00:00', 11.5, 0, 0, 1, 0, 1, 1, 1),
('19:45:00', '06:30:00', '21:00:00', '1:00:00', 10.75, 1, 0, 0, 1, 0, 1, 1),
('14:15:00', '19:00:00', '16:00:00', '0:30:00', 4.75, 1, 1, 0, 1, 1, 0, 0),
('10:30:00', '22:15:00', '12:15:00', '1:00:00', 11.75, 1, 0, 1, 0, 1, 1, 0),
('21:45:00', '05:30:00', '23:00:00', '0:30:00', 7.75, 1, 0, 1, 1, 0, 0, 0),
('20:45:00', '01:00:00', '22:15:00', '0:30:00', 4.25, 1, 1, 1, 0, 0, 1, 1),
('14:00:00', '22:00:00', '16:30:00', '0:30:00', 8, 0, 0, 1, 0, 0, 0, 0),
('17:30:00', '21:45:00', '19:30:00', '0:30:00', 4.25, 0, 1, 0, 1, 0, 0, 0),
('20:30:00', '08:00:00', '22:45:00', '1:00:00', 11.5, 0, 0, 1, 0, 0, 1, 1),
('15:00:00', '01:30:00', '17:00:00', '1:00:00', 10.5, 1, 0, 0, 0, 0, 1, 0),
('19:45:00', '02:15:00', '21:30:00', '0:30:00', 6.5, 0, 0, 0, 1, 1, 0, 1),
('03:00:00', '13:15:00', '05:30:00', '1:00:00', 10.25, 1, 0, 1, 0, 1, 0, 1),
('03:15:00', '13:45:00', '05:15:00', '1:00:00', 10.5, 0, 0, 1, 0, 1, 0, 1),
('03:00:00', '08:45:00', '05:30:00', '0:30:00', 5.75, 0, 0, 1, 0, 0, 1, 0),
('08:15:00', '16:15:00', '10:45:00', '0:30:00', 8, 0, 0, 1, 0, 0, 0, 1),
('04:45:00', '13:15:00', '06:00:00', '1:00:00', 8.5, 1, 1, 1, 1, 0, 0, 1),
('13:15:00', '22:00:00', '15:15:00', '1:00:00', 8.75, 1, 1, 1, 1, 1, 1, 1),
('11:15:00', '18:30:00', '13:00:00', '0:30:00', 7.25, 0, 1, 1, 0, 1, 0, 0),
('21:00:00', '04:15:00', '23:00:00', '0:30:00', 7.25, 1, 1, 0, 0, 1, 0, 0),
('00:00:00', '10:45:00', '02:15:00', '1:00:00', 10.75, 0, 0, 1, 1, 1, 1, 1),
('09:15:00', '20:00:00', '11:00:00', '1:00:00', 10.75, 1, 0, 1, 1, 0, 0, 1),
('12:30:00', '17:15:00', '14:30:00', '0:30:00', 4.75, 0, 0, 1, 0, 0, 0, 0),
('05:15:00', '11:45:00', '07:45:00', '0:30:00', 6.5, 0, 1, 0, 1, 1, 1, 1),
('10:00:00', '15:45:00', '12:00:00', '0:30:00', 5.75, 1, 1, 0, 1, 1, 1, 1),
('08:45:00', '20:30:00', '10:45:00', '1:00:00', 11.75, 0, 1, 0, 0, 1, 0, 1),
('01:45:00', '05:15:00', '03:15:00', '0:30:00', 3.5, 1, 0, 1, 0, 1, 1, 0),
('10:15:00', '15:00:00', '12:15:00', '0:30:00', 4.75, 0, 1, 0, 1, 1, 1, 0),
('21:30:00', '09:00:00', '23:45:00', '1:00:00', 11.5, 1, 0, 1, 0, 0, 0, 1),
('13:45:00', '21:00:00', '15:45:00', '0:30:00', 7.25, 1, 0, 1, 0, 1, 1, 1),
('18:00:00', '23:30:00', '20:00:00', '0:30:00', 5.5, 1, 1, 0, 0, 1, 0, 1),
('22:15:00', '03:45:00', '00:15:00', '0:30:00', 5.5, 1, 0, 1, 1, 0, 0, 1),
('11:30:00', '22:45:00', '13:30:00', '1:00:00', 11.25, 1, 1, 0, 1, 0, 0, 1);
    ''')
    conn.commit()
    conn.close()

def insert3():
    """
    Insert a really small example data set into Tasks and Shifts.
    (For demonstration)
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO TasksTable3 (
            TaskName,
            Day,
            StartTime,
            EndTime,
            Duration,
            NursesRequired
        )
        VALUES
            ('task 1', 'Monday', '09:00:00', '10:00:00', '0:30:00', 4),
            ('task 2', 'Monday', '09:00:00', '10:00:00', '0:30:00', 20),
            ('task 3', 'Monday', '09:00:00', '10:00:00', '0:30:00', 5),
            ('task 4', 'Monday', '09:00:00', '10:00:00', '0:30:00', 11),
            ('task 5', 'Monday', '09:00:00', '10:00:00', '0:30:00', 1),
            ('task 6', 'Monday', '08:30:00', '10:00:00', '0:30:00', 1),
            ('task 7', 'Tuesday', '09:00:00', '10:00:00', '0:30:00', 1),
            ('task 8', 'Tuesday', '09:00:00', '10:00:00', '0:30:00', 20),
            ('task 9', 'Tuesday', '09:00:00', '10:00:00', '0:30:00', 9),
            ('task 10', 'Monday', '12:00:00', '12:30:00', '0:15:00', 5),
            ('task 11', 'Tuesday', '12:00:00', '12:30:00', '0:15:00', 10),
            ('task 12', 'Tuesday', '02:00:00', '04:30:00', '01:00:00', 10),
            ('task 13', 'Monday', '15:00:00', '19:30:00', '01:00:00', 10);

              
    ''')
    conn.commit()
    c.execute('''
        INSERT INTO ShiftsTable6 (
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
            Sunday
        )
        VALUES
            ('07:00:00', '12:00:00', '08:30:00', '0:30:00', 10, 1, 1, 1, 1, 1, 1, 1),
            ('07:30:00', '12:30:00', '08:30:00', '0:30:00', 20, 1, 1, 1, 1, 1, 1, 1),
            ('00:30:00', '04:30:00', '01:30:00', '0:30:00', 5, 1, 1, 1, 1, 1, 1, 1),
            ('14:30:00', '19:30:00', '17:30:00', '0:30:00', 5, 1, 1, 1, 1, 1, 1, 1);
           
    ''')
    conn.commit()
    conn.close()

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
    tasks_df = get_all("TasksTable3")
    shifts_df = get_all("ShiftsTable6")

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

    # Column names in ShiftsTable6 for the days of the week
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
                    vtype=GRB.CONTINUOUS, lb=0, name=var_name
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
 
   
    # --- 7. Solve the model ---
    with st.spinner("Optimizing tasks and shifts. Please wait..."):
        try:
            model.optimize()
        except GurobiError as e:
            st.error(f"Gurobi error occurred: {e}")
            return

    if model.status == GRB.OPTIMAL:
        # Phase 1: Collect raw assignment data and calculate contributions
        from collections import defaultdict
        from datetime import datetime, date
        temp_results = []
        shift_day_cost = defaultdict(float)        # Total cost per (shift, day)
        shift_day_contributions = defaultdict(float)  # Sum of contributions
        
        for (task_id, shift_id, d), assign_var in task_shift_vars.items():
            if assign_var.x > 0.5:
                # Get basic assignment info
                workers = shift_worker_vars[(shift_id, d)].x
                shift_weight = shifts_df.loc[shift_id, "Weight"]
                task_row = tasks_df.loc[task_id]
                
                # Calculate task duration in hours
                t_start = task_row["StartTime"]
                t_end = task_row["EndTime"]
                start_dt = datetime.combine(date.min, t_start)
                end_dt = datetime.combine(date.min, t_end)
                duration = (end_dt - start_dt).total_seconds() / 3600
                
                # Calculate contribution metric (nurses × hours)
                contribution = task_row["NursesRequired"] * duration
                
                # Store temporary data
                temp_results.append({
                    "task_id": task_id,
                    "shift_id": shift_id,
                    "day": d,
                    "workers": workers,
                    "shift_weight": shift_weight,
                    "contribution": contribution
                })
                
                # Update aggregates
                shift_day_cost[(shift_id, d)] = workers * shift_weight
                shift_day_contributions[(shift_id, d)] += contribution

        # Phase 2: Calculate proportional costs

        def calculate_cost_for_intervals(task_rows, shift_row, weight, interval_minutes=15):
            """
            Calculate the cost considering shift breaks, preventing task assignments during break times.
            Returns assignments, total cost, and max nurses required.
            """
            shift_start = pd.to_datetime(shift_row["StartTime"], format="%H:%M:%S")
            shift_end = pd.to_datetime(shift_row["EndTime"], format="%H:%M:%S")
            
            break_start = pd.to_datetime(shift_row["BreakTime"], format="%H:%M:%S")
            break_duration = pd.Timedelta(minutes=int(pd.to_datetime(shift_row["BreakDuration"], format="%H:%M:%S").minute))
            break_end = break_start + break_duration

            # Create time slots excluding break period
            time_slots = {}
            periods = []
            
            # Add pre-break period if valid
            if shift_start < break_start:
                periods.append((shift_start, break_start))
            
            # Add post-break period if valid
            if break_end < shift_end:
                periods.append((break_end, shift_end))
            
            # Create time slots for each valid period
            for period_start, period_end in periods:
                for minute in range(int(period_start.timestamp() // 60), 
                                int(period_end.timestamp() // 60)):
                    time_slots[minute] = 0

            assignments = []

            for task_row in task_rows:
                task_start = pd.to_datetime(task_row["StartTime"], format="%H:%M:%S")
                task_end = pd.to_datetime(task_row["EndTime"], format="%H:%M:%S")

                try:
                    duration_minutes = int(task_row["Duration"])
                except ValueError:
                    duration_td = pd.to_timedelta(task_row["Duration"])
                    duration_minutes = int(duration_td.total_seconds() / 60)

                best_start = None
                best_cost = float("inf")
                valid_start_times = []

                # Find valid start times in each available period
                for period_start, period_end in periods:
                    # Adjust for task constraints
                    start_time = max(task_start, period_start)
                    end_time = min(task_end, period_end)
                    
                    if start_time >= end_time:
                        continue  # No valid time in this period

                    # Generate possible start times within this period
                    period_starts = pd.date_range(
                        start=start_time,
                        end=end_time - pd.Timedelta(minutes=duration_minutes),
                        freq=f"{interval_minutes}min"
                    )
                    valid_start_times.extend(period_starts)

                if not valid_start_times:
                    continue  # No valid placement for this task

                # Evaluate each valid start time
                for start in valid_start_times:
                    end = start + pd.Timedelta(minutes=duration_minutes)
                    
                    # Verify the task doesn't overlap with break
                    if (start < break_end) and (end > break_start):
                        continue  # Skip times overlapping with break

                    temp_slots = time_slots.copy()
                    valid = True
                    
                    # Check all minutes in the task duration
                    for t in range(int(start.timestamp() // 60), 
                                int(end.timestamp() // 60)):
                        if t not in temp_slots:
                            valid = False
                            break
                        temp_slots[t] += task_row["NursesRequired"]

                    if not valid:
                        continue  # Invalid placement

                    current_max = max(temp_slots.values(), default=0)
                    cost = current_max * weight

                    if cost < best_cost or (cost == best_cost and not best_start):
                        best_cost = cost
                        best_start = start

                if best_start:
                    assignments.append({
                                            "Task ID": task_row["id"],
                                            "Task Name": task_row["TaskName"],
                                            "Day": task_row["Day"],
                                            "Task Start": task_row["StartTime"],
                                            "Task End": task_row["EndTime"],
                                            "Begin Task": best_start,
                                            "End Task": best_start + pd.Timedelta(minutes=duration_minutes),
                                            "Workers Assigned": task_row["NursesRequired"]
                                        })

                    # Update actual time slots
                    for t in range(int(best_start.timestamp() // 60), 
                                int((best_start + pd.Timedelta(minutes=duration_minutes)).timestamp() // 60)):
                        time_slots[t] += task_row["NursesRequired"]

            max_nurses = max(time_slots.values(), default=0)
            total_cost = max_nurses * weight
            return assignments, total_cost, max_nurses
        

        # Compute results
        processed_shifts = set()
        results = []
        daily_costs = {day: 0.0 for day in day_names}
        daily_workers = {day: 0 for day in day_names}
        daily_tasks = {day: 0 for day in day_names}
        for entry in temp_results:
            shift_id = entry["shift_id"]
            day = entry["day"]
            key = (shift_id, day)

            # if shift_id in processed_shifts:
            #     continue  # Skip already processed shifts

            if key in processed_shifts:
                continue
            processed_shifts.add(key)

            shift_row = shifts_df.loc[shift_id]
            weight = shift_row["Weight"]
            #key = (shift_id, entry["day"])

            # Filter tasks for the current shift
            relevant_tasks = [
                tasks_df.loc[task["task_id"]]
                for task in temp_results
                if task["shift_id"] == shift_id and task["day"] == day
            ]

            # Compute optimal intervals and costs
            assignments, total_cost, max_nurses  = calculate_cost_for_intervals(relevant_tasks, shift_row, weight)
            daily_costs[day] += total_cost
            daily_workers[day] += max_nurses
            daily_tasks[day] += len(assignments)  # Count assigned tasks

            # Collect results for each task
            for assignment in assignments:
                results.append({
                    "Task ID": assignment["Task ID"],
                    "Task Name": assignment["Task Name"],
                    "Day": assignment["Day"],
                    "Task Start": assignment["Task Start"].strftime("%H:%M"),
                    "Task End": assignment["Task End"].strftime("%H:%M"),
                    "Begin Task": assignment["Begin Task"].strftime("%H:%M"),
                    "End Task": assignment["End Task"].strftime("%H:%M"),
                    "Shift ID": shift_row["id"],
                    "Shift Start": shift_row["StartTime"].strftime("%H:%M"),
                    "Shift End": shift_row["EndTime"].strftime("%H:%M"),
                    "Workers Assigned": assignment["Workers Assigned"],
                    "Hourly Rate (€)": weight,
                    "Task Cost (€)":  round(assignment["Workers Assigned"] * weight, 2) ,
                    "Number of Nurses": max_nurses,
                    "Cost %": round((total_cost / shift_day_cost[key]) * 100, 1) if shift_day_cost[key] > 0 else 0
                })

            #processed_shifts.add(shift_id)  # Mark this shift as processed

        # Convert results to DataFrame
        results_df = pd.DataFrame(results)

        results_df["Shift"] = (
            results_df["Shift Start"] 
            + " - " 
            + results_df["Shift End"]
        )

       
        # 1. Cost Validation Check
        validation = results_df.groupby(["Shift ID", "Day"]).agg(
            Total_Cost=("Task Cost (€)", "sum"),
            Expected_Cost=("Hourly Rate (€)", lambda x: x.iloc[0] * results_df["Workers Assigned"].iloc[0])
        ).reset_index()
        validation["Valid"] = validation["Total_Cost"].round(2) == validation["Expected_Cost"].round(2)
 
        day_summary = []
        for day in day_names:
            day_summary.append({
                "Day": day,
                "Total Cost (€)": round(daily_costs[day], 2),
                "Tasks Assigned": daily_tasks[day],
                "Workers Assigned": daily_workers[day]
            })


        day_summary_df = pd.DataFrame(day_summary)

        results_df["Shift"] = results_df["Shift Start"] + " - " + results_df["Shift End"]


        total_cost = 0
        for day in day_names:
            total_cost += round(daily_costs[day], 2)


        # --- Display Results ---
        st.success("✅ Task-shift optimization successful!")
        st.balloons()

        # Overall Metrics
        #total_cost = model.ObjVal
        # total_cost = 7
        total_workers = sum(daily_workers.values())
        total_tasks = len(results_df)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Cost", f"€{total_cost:,.2f}")
        col2.metric("Total Workers Assigned", total_workers)
        col3.metric("Total Tasks Assigned", total_tasks)

        # Detailed Assignments
        with st.expander("📋 View Detailed Task Assignments", expanded=True):
            if not results_df.empty:
                st.dataframe(
                    results_df.iloc[:,[1,2,5,6,7,10]],
                    column_order=(
                        #"Task ID",
                          "Task Name",
                                   "Day", 
                                  # "Task Start", "Task End",
                                   "Begin Task","End Task",
                                  "Shift ID", 
                                 # "Shift Start", "Shift End",
                                    "Workers Assigned"),
                    hide_index=True
                )
                st.download_button(
                    label="Download Assignments as CSV",
                    data=results_df.to_csv(index=False).encode("utf-8"),
                    file_name="task_assignments.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No tasks were assigned.")

        # 1. Group results_df to get nurse requirements
        nurse_requirements_df = (
            results_df
            .groupby(["Day", "Shift ID", "Shift Start", "Shift End"], as_index=False)
            .agg({
                "Number of Nurses": "max",  # Peak nurses from shift optimization
                "Task Cost (€)": "sum"      # Total shift cost
            })
        )

        # 2. Merge the nurse_requirements_df with shifts_df to pull in the 'Weight' column
        #    Rename 'id' to 'Shift ID' in the shifts_df slice for cleaner merge:
        shifts_weight_df = shifts_df[['id', 'Weight']].rename(columns={'id': 'Shift ID'})
        nurse_requirements_df = nurse_requirements_df.merge(shifts_weight_df, on="Shift ID", how="left")

        with st.expander("👩‍⚕️ View Nurse Requirements per Shift per Day", expanded=True):
            if not nurse_requirements_df.empty:
                # Create a combined "Shift" column for display (Start - End)
                nurse_requirements_df["Shift"] = (
                    nurse_requirements_df["Shift Start"] + " - " + nurse_requirements_df["Shift End"]
                )
                
                # 3. Decide which columns to show in your table
                display_df = nurse_requirements_df[[
                    "Day", 
                    "Shift", 
                    "Shift ID", 
                    "Number of Nurses",
                    "Weight"  # <-- newly included column
                ]]
                
                # Show data
                st.dataframe(
                    display_df,
                    column_order=["Day", "Shift", "Shift ID", "Number of Nurses", "Weight"],
                    hide_index=True
                )

                # Optional download button
                st.download_button(
                    label="Download Nurse Requirements as CSV",
                    data=display_df.to_csv(index=False).encode("utf-8"),
                    file_name="nurse_requirements.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No nurse requirements found.")



        # Daily Summary
        with st.expander("📅 Daily Summary", expanded=True):
            st.dataframe(
                day_summary_df,
                column_order=("Day", "Total Cost (€)", "Tasks Assigned", "Nurses Assigned"),
                hide_index=True
            )
            st.download_button(
                label="Download Daily Summary as CSV",
                data=day_summary_df.to_csv(index=False).encode("utf-8"),
                file_name="daily_summary.csv",
                mime="text/csv"
            )
    
        with st.expander("Graphical Summaries 📊", expanded=True):
            if not results_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    # Ensure we have data to plot
                    if not results_df.empty:
                        fig = px.pie(day_summary_df, names='Day', values='Total Cost (€)', title='<b>Cost Distribution by Day</b>')
                        fig.update_layout(showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No data available for pie chart")

                with col2:
                    # Ensure we have data to plot
                    if not nurse_requirements_df.empty:
                        # 1. Group by Shift ID to sum the total number of nurses across all days
                        #    and grab the first (or any consistent) shift Weight for that ID
                        shift_sum_df = nurse_requirements_df.groupby("Shift ID", as_index=False).agg({
                            "Number of Nurses": "sum",    # sum across all days
                            "Weight": "first"            # or "max"/"min" if you expect it to be consistent
                        })
                        
                        # 2. Calculate total cost for each shift
                        shift_sum_df["TotalShiftCost"] = shift_sum_df["Number of Nurses"] * shift_sum_df["Weight"]

                        # 3. Create a bar plot for these aggregated costs
                        fig = px.bar(
                            shift_sum_df,
                            x="Shift ID",
                            y="TotalShiftCost",
                            title="<b>Total Cost by Shift</b>",
                            text="TotalShiftCost"  # optional: show the value on top of each bar
                        )
                        fig.update_layout(showlegend=False)
                        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")  # format the cost nicely
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No data available for bar chart")
            else:
                st.warning("No results to visualize") 

            # Gantt chart  
            st.subheader("Gantt Charts by Day")

            # Ensure the columns we need actually exist
            if not {"Day", "Task Name", "Shift ID", "Begin Task", "End Task"}.issubset(results_df.columns):
                st.warning("Required columns for Gantt chart not found in results_df.")
            else:
                
                unique_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                for day in unique_days:
                    day_data = results_df[results_df["Day"] == day].copy()
                    
                    if day_data.empty:
                        continue  # Skip if no tasks on that day
    
                    day_data["Begin"] = pd.to_datetime(day_data["Begin Task"], format="%H:%M").apply(
                        lambda t: t.replace(year=2000, month=1, day=1)
                    )
                    day_data["End"] = pd.to_datetime(day_data["End Task"], format="%H:%M").apply(
                        lambda t: t.replace(year=2000, month=1, day=1)
                    )
                    
                    # Plotly Express timeline
                    fig = px.timeline(
                        day_data,
                        x_start="Begin",
                        x_end="End",
                        y="Task Name",
                        color="Shift ID",  # Same color for the same shift
                        hover_data=["Task Name", "Shift ID"]
                    )
                    
                    # Reverse the Y-axis so tasks list top-to-bottom
                    fig.update_yaxes(autorange="reversed")
                    
                    # Format the X-axis ticks to show just HH:MM
                    fig.update_layout(
                        title=f"Gantt Chart for {day}",
                        xaxis=dict(tickformat='%H:%M'),
                        height=300  
                    )

                    st.plotly_chart(fig, use_container_width=True)

 
    else:
        st.error(f"Optimization failed with status: {model.status}")
        # Optional: Add infeasibility diagnostics
        model.computeIIS()
        for constr in model.getConstrs():
            if constr.IISConstr:
                st.write(f"⚠️ Infeasible constraint: {constr.constrName}")


# ------------------------------------------------------------------
#                          Visualization
# ------------------------------------------------------------------
def display_tasks_and_shifts():
    """Modern interactive visualization of tasks and shifts with enhanced UI."""
    st.header(" Schedule Visualization Dashboard", divider="rainbow")

    # Get data with loading state
    with st.spinner("Loading scheduling data..."):
        tasks_df = get_all("TasksTable3")
        shifts_df = get_all("ShiftsTable6")

    # Show empty state if no data
    if tasks_df.empty and shifts_df.empty:
        st.info("🌟 No tasks or shifts found. Add data to get started!")
        _,_, col, _, _ = st.columns([1, 1, 1,1,1])  # Ratio creates centered middle column
        with col:
            st.markdown(
            '<div style="display: flex; justify-content: center;">'
            '<img src="https://cdn-icons-png.flaticon.com/512/7486/7486744.png" width="200"/>'
            '</div>',
            unsafe_allow_html=True
            )
        return

    # Metrics cards at the top
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📋 Total Tasks", len(tasks_df))
    with col2:
        st.metric("👥 Total Shifts", len(shifts_df))
    with col3:
        avg_duration = pd.to_timedelta(tasks_df['Duration']).mean().total_seconds()/3600 if not tasks_df.empty else 0
        st.metric("⏳ Avg Task Duration", f"{avg_duration:.1f} hours")

    # Tabs for different views
    tab1, tab2 = st.tabs(["📊 Enhanced Gantt Charts", "📁 Raw Data"])

    with tab1:
        try:
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                        "Friday", "Saturday", "Sunday"]
            time_range = ["2023-01-01 00:00:00", "2023-01-01 23:59:59"]

            if not tasks_df.empty:
                st.subheader("🔧 Task Schedule", divider="blue")
                tasks_df = tasks_df.assign(
                    Start=lambda df: pd.to_datetime("2023-01-01 " + df['StartTime']),
                    End=lambda df: pd.to_datetime("2023-01-01 " + df['EndTime']),
                    Day=lambda df: pd.Categorical(df['Day'], categories=day_order, ordered=True),
                    DurationHours=lambda df: (df['End'] - df['Start']).dt.total_seconds()/3600
                ).sort_values(by=['Day', 'Start'])

                fig_tasks = px.timeline(
                    tasks_df,
                    x_start="Start",
                    x_end="End",
                    y="Day",
                    color="TaskName",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    hover_data={
                        "TaskName": True,
                        "NursesRequired": True,
                        "DurationHours": ":.1f hours",
                        "Start": "|%H:%M",
                        "End": "|%H:%M"
                    },
                    title="<b>Task Distribution by Day</b>",
                    template="plotly_white"
                )
                fig_tasks.update_layout(
                    height=600,
                    hovermode="y unified",
                    xaxis_title="Time of Day",
                    yaxis_title="",
                    legend_title="Tasks",
                    font=dict(family="Arial", size=12),
                    margin=dict(l=100, r=20, t=60, b=20)
                )
                fig_tasks.update_xaxes(
                    tickformat="%H:%M",
                    dtick=3600000,
                    range=time_range,
                    showgrid=True
                )
                st.plotly_chart(fig_tasks, use_container_width=True)

            # Interactive shift visualization
            if not shifts_df.empty:
                st.subheader("👥 Shift Schedule", divider="green")
                shifts_df["Start"] = pd.to_datetime("2023-01-01 " + shifts_df["StartTime"])
                shifts_df["End"] = pd.to_datetime("2023-01-01 " + shifts_df["EndTime"])

                # Expand shifts with weight information
                shift_expanded = []
                for _, row in shifts_df.iterrows():
                    for day in day_order:
                        if row[day] == 1:
                            shift_expanded.append({
                                "ShiftID": row["id"],
                                "Day": day,
                                "Start": row["Start"],
                                "End": row["End"],
                                "Weight": row["Weight"],
                                "NursesAllocated": row.get("NursesAllocated", "N/A")
                            })
                shifts_expanded_df = pd.DataFrame(shift_expanded)
                shifts_expanded_df["Day"] = pd.Categorical(
                    shifts_expanded_df["Day"], 
                    categories=day_order, 
                    ordered=True
                ).sort_values()

                fig_shifts = px.timeline(
                    shifts_expanded_df,
                    x_start="Start",
                    x_end="End",
                    y="Day",
                    color="Weight",
                    color_continuous_scale=px.colors.sequential.Blues,
                    hover_data={
                        "ShiftID": True,
                        "NursesAllocated": True,
                        "Weight": ":.1f",
                        "Start": "|%H:%M",
                        "End": "|%H:%M"
                    },
                    title="<b>Shift Schedule by Weight</b>",
                    template="plotly_white"
                )
                fig_shifts.update_layout(
                    height=600,
                    xaxis_title="Time of Day",
                    yaxis_title="",
                    font=dict(family="Arial", size=12),
                    coloraxis_colorbar=dict(title="Shift Weight"),
                    margin=dict(l=100, r=20, t=60, b=20)
                )
                fig_shifts.update_xaxes(
                    tickformat="%H:%M",
                    dtick=3600000,
                    range=time_range
                )
                st.plotly_chart(fig_shifts, use_container_width=True)

        except Exception as e:
            st.error(f"🚨 Visualization error: {str(e)}")
            st.info("Please ensure Plotly is installed: `pip install plotly`")

    with tab2:

        if not tasks_df.empty:
            with st.expander("📋 Task Details", expanded=True):
                st.dataframe(
                    tasks_df.iloc[:, 1:7].style
                    .background_gradient(subset=["NursesRequired"], cmap="Blues"),
                    use_container_width=True,
                    height=300
                )
                st.download_button(
                    label="📥 Download Tasks CSV",
                    data=tasks_df.iloc[:, 1:7].to_csv(index=False).encode("utf-8"),
                    file_name="hospital_tasks.csv",
                    mime="text/csv",
                    type="primary"
                )

        if not shifts_df.empty:
            with st.expander("👥 Shift Details", expanded=True):
                st.dataframe(
                    shifts_df.iloc[:, 1:13].style
                    .highlight_max(subset=["Weight"], color="#fffd75")
                    .highlight_min(subset=["Weight"], color="#90EE90"),
                    use_container_width=True,
                    height=300
                )
                st.download_button(
                    label="📥 Download Shifts CSV",
                    data=shifts_df.iloc[:, 1:13].to_csv(index=False).encode("utf-8"),
                    file_name="hospital_shifts.csv",
                    mime="text/csv",
                    type="primary"
                )

    # Visual divider
    st.markdown("---")
    st.caption("💡 Tip: Hover over charts for detailed information. Click legend items to filter categories.")

def header():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
        
        .modern-header {
            font-family: 'Poppins', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1.5rem;
            padding: 1.5rem;
            margin: 2rem 0;
            background: linear-gradient(135deg, #0066ff 0%, #00ccff 100%);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 102, 255, 0.2);
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .modern-header:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 102, 255, 0.3);
        }

        .modern-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 50%;
            height: 100%;
            background: linear-gradient(
                to right,
                rgba(255, 255, 255, 0) 0%,
                rgba(255, 255, 255, 0.2) 50%,
                rgba(255, 255, 255, 0) 100%
            );
            transform: skewX(-20deg);
            transition: left 0.8s ease-out;
        }

        .modern-header:hover::before {
            left: 200%;
        }

        .header-logo {
            height: 5rem;
            width: auto;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
            transition: transform 0.3s ease;
        }

        .header-text {
            color: #ffffff;
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.5px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            background: linear-gradient(90deg, #fff, #e6f3ff);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-container {
            animation: fadeIn 0.8s ease-out;
        }

        @media (max-width: 768px) {
            .modern-header {
                flex-direction: column;
                padding: 1rem;
            }
            
            .header-text {
                font-size: 2rem;
                text-align: center;
            }
            
            .header-logo {
                height: 4rem;
            }
        }

        /* Enhanced general transitions */
        .stButton button, .stDownloadButton button, .stExpander, .metric-box {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            will-change: transform, box-shadow;
        }

        .stButton button {
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }

        .stButton button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
        }

        .stExpander {
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
            padding: 8px !important;
            margin: 12px 0 !important;
        }

        .stExpander:hover {
            border-color: #2196F3 !important;
            box-shadow: 0 4px 12px rgba(33, 150, 243, 0.1) !important;
        }

        .stExpander .streamlit-expanderHeader {
            transition: color 0.2s ease, background 0.3s ease !important;
            border-radius: 8px !important;
        }

        .stExpander .streamlit-expanderHeader:hover {
            color: #2196F3 !important;
            background: rgba(33, 150, 243, 0.05) !important;
        }

        /* Enhanced dataframe styling */
        .stDataFrame {
            border-radius: 12px !important;
            overflow: hidden !important;
            transition: box-shadow 0.3s ease !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }

        .stDataFrame:hover {
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15) !important;
        }

        /* Modern metric cards */
        .metric-box {
            background: linear-gradient(135deg, #ffffff, #f8f9fa) !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
            padding: 20px !important;
            margin: 10px 0 !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05) !important;
        }

        .metric-box:hover {
            transform: translateY(-5px) !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1) !important;
            border-color: #2196F3 !important;
        }

        /* Enhanced input fields */
        .stTextInput input, .stNumberInput input, .stSelectbox select {
            transition: all 0.3s ease !important;
        }

        .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
            border-color: #2196F3 !important;
            box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.2) !important;
        }

        /* Chart hover effects */
        .plotly-graph-div {
            transition: transform 0.3s ease !important;
            border-radius: 16px !important;
            overflow: hidden !important;
        }

        .plotly-graph-div:hover {
            transform: translateY(-3px) scale(1.005) !important;
        }

        /* Enhanced tabs */
        .stTabs [role="tablist"] {
            gap: 8px !important;
            margin: 16px 0 !important;
             t
        }

        .stTabs [role="tab"] {
            transition: all 0.3s ease !important;
            border-radius: 8px 8px 0 0 !important;
            padding: 12px 24px !important;
            border: none !important;
            position: relative;
            background: transparent !important;
        }

        .stTabs [role="tab"]:hover {
            background: rgba(33, 150, 243, 0.1) !important;
            color: #2196F3 !important;
        }

        .stTabs [aria-selected="true"] {
            color: #2196F3 !important;
        }

        /* Smooth animated underline */
        .stTabs [aria-selected="true"]::after {
            content: "";
            position: absolute;
            bottom: -1px;
            left: 0;
            right: 0;
            height: 3px;
            background: "transparent";
            border-radius: 2px;
            animation: tabSlide 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        @keyframes tabSlide {
            from {
                transform: scaleX(0.8);
                opacity: 0;
            }
            to {
                transform: scaleX(1);
                opacity: 1;
            }
        }

        /* Remove default indicator */
        .stTabs [role="tablist"] button[aria-selected="true"] {
            box-shadow: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Configuration for PNG
    HEADER_LOGO_PATH = "56566395.png"
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(parent_dir, "56566395.png")

    def get_png_header():
        try:
            with open(logo_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'''
            <div class="header-container">
                <div class="modern-header">
                    <img src="data:image/png;base64,{b64}" class="header-logo"/>
                    <span class="header-text">Hospital Staff Scheduling System</span>
                </div>
            </div>
            '''
        except FileNotFoundError:
            st.error(f"Header logo missing: {logo_path}")
            st.stop()

    # Display header
    st.markdown(get_png_header(), unsafe_allow_html=True)

def show_contact():
    st.title("Contact Us")

    # Add a description or introductory text
    st.write("We'd love to hear from you! Please use the form below to get in touch with us.")

    # Contact form
    with st.form("contact_form"):
        # Name input
        name = st.text_input("Name", placeholder="Enter your name")
        # Email input
        email = st.text_input("Email", placeholder="Enter your email address")
        # Message input
        message = st.text_area("Message", placeholder="Write your message here", height=150)
        # Submit button
        submitted = st.form_submit_button("Submit")

        # Handle form submission
        if submitted:
            if name and email and message:
                st.success("Thank you for your message! We'll get back to you shortly.")
                # You can add email sending functionality here, e.g., using an API like SendGrid
            else:
                st.error("Please fill in all fields before submitting.")

    # Additional contact information
    st.write("### Other Ways to Reach Us")
    st.write("📧 Email: support@vuamsterdamscheduling.com")
    st.write("📍 Address: De Boelelaan 1105, 1081 HV Amsterdam, North Holland, Netherlands")
# ------------------------------------------------------------------
#                            Main App
# ------------------------------------------------------------------

def main():
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(parent_dir, "56566395.png")
 
    st.set_page_config(page_title="Hospital Scheduler", layout="wide", page_icon=logo_path)
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .header-style {
            font-size: 2em !important;
            color: #2c3e50 !important;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .info-box {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    init_db()
    home_tab, manual_tab, contact_tab = st.tabs(["🏠 Home", "📖 Manual","📞 Contact"])
    
    with home_tab:
        header()
        
        # Create two main columns
        left_col, right_col = st.columns([1.15, 2.85])
        
        with left_col:
            # Manual Input Section
            with st.expander("➕ Add Tasks/Shifts Manually"):
                task_input_form()
                shift_input_form()
            
            # Bulk Upload Section
            with st.expander("📤 Bulk Upload Data", expanded=True):
                upload_tasks_excel()
                upload_shifts_excel()
                st.markdown("---")
                st.write("Download templates:")
                task_template_download()
                shift_template_download()
            
            # Data Management
            st.markdown("---")
            st.write("**Data Management**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧹 Clear All Tasks", use_container_width=True):
                    clear_all("TasksTable3")
                    st.success("All tasks cleared!")
            with col2:
                if st.button("🧹 Clear All Shifts", use_container_width=True):
                    clear_all("ShiftsTable6")
                    st.success("All shifts cleared!")
            
            # Example Data
            with st.expander("🔍 Load Example Data"):
                ex_col1, ex_col2, ex_col3 = st.columns(3)
                with ex_col1:
                    if st.button("🌱 Really Small Data", use_container_width=True):
                        insert3()
                        st.success("Really small example data loaded!")
                with ex_col2:
                    if st.button("🌲 Small Data", use_container_width=True):
                        insert()
                        st.success("Small example data loaded!")
                with ex_col3:
                    if st.button("🌳 Large Data", use_container_width=True):
                        insert2()
                        st.success("Large example data loaded!")

        with right_col:
            # Visualization and Optimization Tabs
            viz_tab, opt_tab = st.tabs(["📊 Visualization", "⚙️ Optimization"])
            
            with viz_tab:
                display_tasks_and_shifts()
            with opt_tab:
                st.markdown("### Task-Shift Assignment Optimization")
                st.info("Assign tasks to shifts considering time windows and nurse requirements")
                if st.button("🚀 Run Task Optimization ", use_container_width=True):
                    optimize_tasks_with_gurobi()
 
               
    with contact_tab:
        show_contact()

    with manual_tab:
        # --- Title ---
        st.header("User Manual")

        # --- Story Intro ---
        st.write("""
        In a bustling hospital environment, coordinating nurse schedules can be a huge challenge.
        You need to cover all patient-related tasks while ensuring fairness for staff and minimizing
        staffing costs. That's where this app steps in: it helps plan and optimize nurse shifts so
        that every task is covered at the right time by the right number of nurses.
        """)

        # --- Section 1: Overview ---
        st.subheader("1. Overview")
        st.write("""
        This system allows you to manage tasks (like “Administer Medication” or “Physical Therapy”)
        and shifts (e.g., morning, evening, or night shifts). Once you enter your data, you can run 
        an **Optimization** routine that decides how many nurses are needed for each shift to cover 
        every task. Additionally, you can download the final assignment or view it in multiple charts.
        """)

        # --- Section 2: Step-by-Step Guide ---
        st.subheader("2. Step-by-Step Guide")

        # 2.1 Add Tasks Manually
        st.markdown("**2.1 Add Tasks Manually**")
        st.write("""
        - Go to the **Home** tab.
        - In the sidebar section **“Add Tasks/Shifts Manually”**, find the **Task** form.
        - Enter a *Task Name* (e.g., “Wound Care”), select the *Day of the Week*, specify
        *Start Time* and *End Time*, pick the *Duration*, and indicate how many nurses are required.
        - Click **“Add Task”** to save.
        """)

        # 2.2 Add Shifts Manually
        st.markdown("**2.2 Add Shifts Manually**")
        st.write("""
        - Still under **“Add Tasks/Shifts Manually”**, switch to the **Shift** form.
        - Choose the *Shift Start Time* and *Shift End Time* from the dropdowns.
        - Set a *Break Time* and *Break Duration*, if relevant.
        - Adjust the *Shift Weight* (think of this as the cost or difficulty level to cover that shift).
        - Select the days of the week on which this shift is active by toggling them on or off.
        - Click **“Add Shift”** to save.
        """)

        # 2.3 Bulk Upload (Excel/CSV)
        st.markdown("**2.3 Bulk Upload (Excel/CSV)**")
        st.write("""
        - Still in the **Home** tab, under **“Bulk Upload Data”**, you can choose to upload tasks
        or shifts in bulk from a spreadsheet or CSV.
        - Use the provided download templates to see the required columns.
        - Once your data file is ready, upload it via **“Upload Task Excel”** or 
        **“Upload Shifts File”**. The app automatically inserts each row into the system.
        """)

        st.markdown("**2.4 Example Data**")
        st.write("""
        - If you just want to explore or test, you can use the already made example datasets for tasks and shifts 
        by clicking **“Load Example Data”**.
        - These options quickly fill the system with sample entries so you can see how it all works.
        """)

        # 2.5 Clearing Data
        st.markdown("**2.5 Clearing Data**")
        st.write("""
        - If you need to start fresh, simply click **“Clear All Tasks”** or **“Clear All Shifts.”**
        - This removes all existing records, allowing you to upload or enter new data from scratch.
        """)

        # --- Section 3: Visualization ---
        st.subheader("3. Viewing Schedules & Data")
        st.write("""
        In the **Visualization** panel (still under **Home**): you can visualize the  data you imported
        - See a **Gantt-style** timeline for tasks and shifts.
        - Hover over any bar to reveal more details (start/end times, day of the week, etc.).
        - Switch to the **Raw Data** tab to directly browse tables for tasks and shifts, 
        and download them as needed. 
        """)


        st.subheader("4. Running the Optimization")
        st.write("""
        After you have your tasks and shifts set up, you can let the app do the heavy lifting:
        - In the **Home** tab, find the **“Optimization”** section on the right.
        - Click **“Run Task Optimization”** and watch the progress bar.
        - When it’s done, you’ll see a summary of:
        1. **Detailed Assignments** – Which tasks go into which shift/day, how many nurses are 
            assigned, and the cost of each task.
        2. **Nurse Requirements** – An overview of how many nurses are needed for each shift
            on each day.
        3. **Daily Summary** – Total cost per day, the number of tasks covered, and how many 
            nurses in total are allocated.
        4. **Visual Charts** – A pie chart for cost by day and a bar chart for cost by shift.
        """)

        # --- Section 5: Tips & Troubleshooting ---
        st.subheader("5. Tips & Troubleshooting")
        st.write("""
        - **Always confirm your times** – Tasks or shifts that start after they end 
        won’t work as expected.
        - **Check the days** – Make sure the shift you create is active on the same day
        as the task you want to cover.
        - **Invalid Upload** – If the CSV/Excel file is missing columns or uses the 
        wrong format, an error will appear.
        - **No Results?** – Verify you actually have tasks and shifts before running 
        the optimization.
        """)

        # --- Section 6: Questions or Feedback ---
        st.subheader("6. Questions or Feedback")
        st.write("""
        If you have any questions, need guidance, or would like to report an issue,
        head over to the **Contact** tab in the main navigation. Fill in your name,
        email address, and message, then click **Submit**. We’ll be in touch shortly.
        """)

        # Final note
        st.markdown("---")
        st.write("**We hope this system helps you efficiently schedule nurses and deliver the best care possible!**")

if __name__ == "__main__":
    main()
