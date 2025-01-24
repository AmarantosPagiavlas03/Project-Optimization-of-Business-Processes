import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
from datetime import time
import io  
import datetime as dt
from database import add_task_to_db, add_shift_to_db, add_worker_to_db, init_db



# ------------------------------------------------------------------
#                         Form Inputs
# ------------------------------------------------------------------

def generate_time_intervals():
    intervals = [time(hour=h, minute=m) for h in range(24) for m in range(0, 60, 15)]
    intervals.append(time(0, 0))  # Add 24:00 as 00:00
    return intervals

def get_default_indices_for_intervals(intervals):
    """
    Given a list of 15-minute interval times (e.g., [datetime.time(0,0), datetime.time(0,15), ...]),
    this function returns two indexes:
      - One for (current time + 1 hour), rounded to the nearest 15 minutes
      - One for (current time + 2 hours), rounded to the nearest 15 minutes
    If either rounded time does not appear in the intervals list, default index = 0.
    
    Returns:
        (default_idx_1h, default_idx_2h) : (int, int)
    """
    # 1) Compute times
    now_plus_1h = (dt.datetime.now() + dt.timedelta(hours=1)).time()
    now_plus_2h = (dt.datetime.now() + dt.timedelta(hours=2)).time()

    # 2) Round each to the nearest 15 minutes
    nearest_15_1h = (now_plus_1h.minute // 15) * 15
    default_time_1h = now_plus_1h.replace(minute=nearest_15_1h, second=0, microsecond=0)

    nearest_15_2h = (now_plus_2h.minute // 15) * 15
    default_time_2h = now_plus_2h.replace(minute=nearest_15_2h, second=0, microsecond=0)

    # 3) Find indexes in the intervals list (or use 0 if not found)
    if default_time_1h in intervals:
        default_idx_1h = intervals.index(default_time_1h)
    else:
        default_idx_1h = 0

    if default_time_2h in intervals:
        default_idx_2h = intervals.index(default_time_2h)
    else:
        default_idx_2h = 0

    return default_idx_1h, default_idx_2h

def task_input_form():
    """Sidebar form to add a new task."""
    with st.expander("Add Task", expanded=False):
        with st.form("task_form",border=False):
            if "task_start_time" not in st.session_state:
                st.session_state["task_start_time"] = datetime.now().time()
            if "task_end_time" not in st.session_state:
                st.session_state["task_end_time"] = (datetime.now() + timedelta(hours=1)).time()

            # Generate time intervals for select boxes
            intervals = generate_time_intervals()

            default_idx_1h, default_idx_2h = get_default_indices_for_intervals(intervals)

            # Create columns for the input fields
            col1, col2, col3, col4,col5,col6,col7 = st.columns(7, gap="small")

            with col1:
                TaskName = st.text_input("Task Name", key="task_name")
            with col2:
                Day = st.selectbox("Day of the Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], key="day_of_week")
            with col3:
                StartTime = st.selectbox("Start Time", options=intervals,index= default_idx_1h, format_func=lambda t: t.strftime("%H:%M"), key="start_time")
            with col4:
                EndTime = st.selectbox("End Time", options=intervals,index= default_idx_2h, format_func=lambda t: t.strftime("%H:%M"), key="end_time")
            with col5:
                duration_hours = st.number_input("Duration Hours", min_value=0, max_value=23, value=1, step=1, key="duration_hours")
            with col6:
                duration_minutes = st.number_input("Duration Minutes", min_value=0, max_value=59, value=0, step=1, key="duration_minutes")
            with col7:
                NursesRequired = st.number_input("Nurses Required", min_value=1, value=1, step=1, key="nurses_required")

            # Add task button
            col8, col9 = st.columns(2, gap="small")
            with col9:
                if st.form_submit_button("Add Task"):
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
    if "shift_start_time" not in st.session_state:
        st.session_state["shift_start_time"] = datetime.now().time()
    if "shift_end_time" not in st.session_state:
        st.session_state["shift_end_time"] = (datetime.now() + timedelta(hours=1)).time()
    if "break_start_time" not in st.session_state:
        st.session_state["break_start_time"] = (datetime.now() + timedelta(hours=2)).time()

    intervals = generate_time_intervals()
    default_idx_1h, default_idx_2h = get_default_indices_for_intervals(intervals)

    with st.expander("Add Shift"):
        with st.form("shift_form",border=False):
            cols  = st.columns(6, gap="small")
            with cols[0]:
                Shift_StartTime = st.selectbox("Shift Start Time", options=intervals, index=default_idx_1h, format_func=lambda t: t.strftime("%H:%M"))
            with cols[1]:
                Shift_EndTime = st.selectbox("Shift End Time", options=intervals,index=default_idx_2h, format_func=lambda t: t.strftime("%H:%M"))
            with cols[2]:
                BreakTime = st.selectbox("Break Start Time", options=intervals, format_func=lambda t: t.strftime("%H:%M"))
            with cols[3]:
                BreakDuration_hours = st.number_input("Break Duration Hours", min_value=0, max_value=23, value=0)
            with cols[4]:
                BreakDuration_minutes = st.number_input("Break Duration Minutes", min_value=0, max_value=59, value=30)
            with cols[5]:
                Weight = st.number_input("Shift Weight", min_value=0.0, value=1.0)

                
            # st.markdown("### Select Days")
            col_days = st.columns(7, gap="small")
            days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            Days = {day: col_days[i].checkbox(day, value=(day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])) for i, day in enumerate(days_of_week)}

            col7, col8 = st.columns(2, gap="small")
            with col8:
                if st.form_submit_button("Add Shift"):
                    shift_data = (
                        f"{Shift_StartTime.hour}:{Shift_StartTime.minute}:00",
                        f"{Shift_EndTime.hour}:{Shift_EndTime.minute}:00",
                        f"{BreakTime.hour}:{BreakTime.minute}:00",
                        str(timedelta(hours=BreakDuration_hours, minutes=BreakDuration_minutes)),
                        Weight,
                        *(1 if Days[day] else 0 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
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

        shift_data = (
            start_time.strftime("%H:%M:%S"),
            end_time.strftime("%H:%M:%S"),
            break_time.strftime("%H:%M:%S"),
            str(break_duration),
            weight,
            *days.values()
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

    # --- CSV version ---
    csv_data = template_df.to_csv(index=False)
    st.download_button(
        label="Download Task Template (CSV)",
        data=csv_data.encode("utf-8"),
        file_name="task_template.csv",
        mime="text/csv",
        key="task_template_download_csv"
    )

    # --- Excel version ---
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        template_df.to_excel(writer, index=False, sheet_name='TaskTemplate')
    st.download_button(
        label="Download Task Template (Excel)",
        data=excel_buffer.getvalue(),
        file_name="task_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="task_template_download_excel"
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

def task_upload_download_form():
    with st.expander("Upload Multipe Tasks", expanded=False):
        # 1. Download Template
        st.subheader("Download Template")
        task_template_download()

        st.markdown("---")

        # 2. Upload user file
        st.subheader("Upload Your Tasks")
        upload_tasks_excel()

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

    # --- CSV version ---
    csv_data = template_df.to_csv(index=False)
    st.download_button(
        label="Download Shift Template (CSV)",
        data=csv_data.encode("utf-8"),
        file_name="shift_template.csv",
        mime="text/csv",
        key="shift_template_download_csv"
    )

    # --- Excel version ---
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        template_df.to_excel(writer, index=False, sheet_name='ShiftTemplate')
    st.download_button(
        label="Download Shift Template (Excel)",
        data=excel_buffer.getvalue(),
        file_name="shift_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="shift_template_download_excel"
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

def shift_upload_download_form():
    with st.expander("Upload Multiple Shifts", expanded=False):
        # 1. Download Template
        st.subheader("Download Template")
        shift_template_download()

        st.markdown("---")

        # 2. Upload user file
        st.subheader("Upload Your Shifts")
        upload_shifts_excel()