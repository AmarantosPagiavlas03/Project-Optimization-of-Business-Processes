import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO

# Database connection and initialization
DB_FILE = "tasks.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # Create the Tasks table
        c.execute('''
        CREATE TABLE if not exists Tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            TaskName TEXT NOT NULL,
            Day TEXT NOT NULL,
            StartTime TEXT NOT NULL,
            EndTime TEXT,
            Duration TEXT NOT NULL,
            NursesRequired INTEGER NOT NULL
        )
        ''')
        conn.commit()
        # Create the shifts table
        c.execute('''
        CREATE TABLE if not exists Shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            StartTime TEXT NOT NULL,
            EndTime TEXT NOT NULL,
            BreakTime TEXT NOT NULL,
            BreakDuration TEXT NOT NULL,
            Weight FOAT NOT NULL,
            Monday INT NOT NULL,
            Tuesday INT NOT NULL,
            Wednesday INT NOT NULL,
            Thursday INT NOT NULL,
            Friday INT NOT NULL,
            Saturday INT NOT NULL,
            Sunday INT NOT NULL,
            Flexibility TEXT NOT NULL,
            Notes TEXT NULL
        )
        ''')
        conn.commit()
    finally:
        if conn:
            conn.close()


def add_task_to_db(TaskName,Day, StartTime,EndTime, Duration,NursesRequired):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO Tasks (TaskName, Day, StartTime,EndTime, Duration, NursesRequired) VALUES (?, ?, ?, ? , ?, ?)",
              (TaskName,Day, StartTime,EndTime, Duration,NursesRequired))
    conn.commit()
    conn.close()

def get_all_tasks(table = 'Tasks'):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table}")
    rows = c.fetchall()
    conn.close()
    df = pd.DataFrame(rows, columns=[desc[0] for desc in c.description])
    return df

def clear_all_tasks():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM Tasks")
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Streamlit app
st.title("Task Scheduler with SQLite Persistence")

# Sidebar for adding tasks
st.sidebar.header("Add Task")

TaskName = st.sidebar.text_input("Task Name", "")
Day = st.sidebar.selectbox("Day of the Week", 
                           [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
StartTime = st.sidebar.time_input("Start Time", value=datetime.now().time())
EndTime = st.sidebar.time_input("End Time", value=datetime.now().time())
duration_hours = st.sidebar.number_input("Duration Hours", min_value=0, max_value=23, value=1)
duration_minutes = st.sidebar.number_input("Duration Minutes", min_value=0, max_value=59, value=0)
NursesRequired = st.sidebar.number_input("Nurses Required", min_value=1, value=1)

# Add task button
if st.sidebar.button("Add Task"):
    if TaskName:
        Duration = timedelta(hours=duration_hours, minutes=duration_minutes)
        add_task_to_db(
            TaskName,
            Day,
            f"{StartTime.hour}:{StartTime.minute}:00",
            f"{EndTime.hour}:{EndTime.minute}:00",
            f"{Duration}",
            f"{NursesRequired}"
        )
        st.sidebar.success(f"Task '{TaskName}' added!")
    else:
        st.sidebar.error("Task name cannot be empty!")

# Sidebar for adding shifts
st.sidebar.header("Add Shift")

# Initialize session state for shift times
if "shift_start_time" not in st.session_state:
    st.session_state["shift_start_time"] = datetime.now().time()
if "shift_end_time" not in st.session_state:
    st.session_state["shift_end_time"] = (datetime.now() + timedelta(hours=1)).time()

 

# Sidebar inputs for shift times with session state
Shift_StartTime = st.sidebar.time_input(
    "Shift Start Time", 
    value=st.session_state["shift_start_time"], 
    key="shift_start_time_input"
)
Shift_EndTime = st.sidebar.time_input(
    "Shift End Time", 
    value=st.session_state["shift_end_time"], 
    key="shift_end_time_input"
)

# Update session state when time inputs are modified
st.session_state["shift_start_time"] = Shift_StartTime
st.session_state["shift_end_time"] = Shift_EndTime
BreakTime = st.sidebar.time_input("Break Start Time", value=(datetime.now() + timedelta(hours=2)).time())
BreakDuration_hours = st.sidebar.number_input("Break Duration Hours", min_value=0, max_value=23, value=0)
BreakDuration_minutes = st.sidebar.number_input("Break Duration Minutes", min_value=0, max_value=59, value=30)
Weight = st.sidebar.number_input("Shift Weight", min_value=0.0, value=1.0)

# Days selection
Days = {
    "Monday": st.sidebar.checkbox("Monday", value=True),
    "Tuesday": st.sidebar.checkbox("Tuesday", value=True),
    "Wednesday": st.sidebar.checkbox("Wednesday", value=True),
    "Thursday": st.sidebar.checkbox("Thursday", value=True),
    "Friday": st.sidebar.checkbox("Friday", value=True),
    "Saturday": st.sidebar.checkbox("Saturday", value=False),
    "Sunday": st.sidebar.checkbox("Sunday", value=False),
}

Flexibility = st.sidebar.text_area("Flexibility Notes", "")
ShiftNotes = st.sidebar.text_area("Additional Notes", "")

# Add shift button

if st.sidebar.button("Add Shift"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO Shifts 
        (StartTime, EndTime, BreakTime, BreakDuration, Weight, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, Flexibility, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"{Shift_StartTime.hour}:{Shift_StartTime.minute}:00",
            f"{Shift_EndTime.hour}:{Shift_EndTime.minute}:00",
            f"{BreakTime.hour}:{BreakTime.minute}:00",
            f"{timedelta(hours=BreakDuration_hours, minutes=BreakDuration_minutes)}",
            Weight,
            int(Days["Monday"]),
            int(Days["Tuesday"]),
            int(Days["Wednesday"]),
            int(Days["Thursday"]),
            int(Days["Friday"]),
            int(Days["Saturday"]),
            int(Days["Sunday"]),
            Flexibility,
            ShiftNotes,
        ),
    )
    conn.commit()
    conn.close()
    st.sidebar.success("Shift added successfully!")

# Display shifts
st.header("Shifts List")
shifts_df = get_all_tasks('Shifts')
if not shifts_df.empty:
    st.dataframe(shifts_df)
else:
    st.write("No shifts added yet.")

# Days selection
Days = {
    "Monday": st.sidebar.checkbox("Monday", value=True, key="Monday_checkbox"),
    "Tuesday": st.sidebar.checkbox("Tuesday", value=True, key="Tuesday_checkbox"),
    "Wednesday": st.sidebar.checkbox("Wednesday", value=True, key="Wednesday_checkbox"),
    "Thursday": st.sidebar.checkbox("Thursday", value=True, key="Thursday_checkbox"),
    "Friday": st.sidebar.checkbox("Friday", value=True, key="Friday_checkbox"),
    "Saturday": st.sidebar.checkbox("Saturday", value=False, key="Saturday_checkbox"),
    "Sunday": st.sidebar.checkbox("Sunday", value=False, key="Sunday_checkbox"),
}

Flexibility = st.sidebar.text_area("Flexibility Notes", "", key="flexibility_text_area")
ShiftNotes = st.sidebar.text_area("Additional Notes", "", key="shift_notes_text_area")



# File uploader to import tasks
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])
if uploaded_file:
    try:
        uploaded_tasks = pd.read_excel(uploaded_file)
        required_columns = {"Task Name", "Start Date", "Start Time", "Duration"}
        if required_columns.issubset(uploaded_tasks.columns):
            for _, row in uploaded_tasks.iterrows():
                add_task_to_db(
                    row["Task Name"],
                    pd.Timestamp(row["Start Date"]).date().isoformat(),
                    str(row["Start Time"]),
                    str(row["Duration"])
                )
            st.sidebar.success("Tasks from the uploaded file have been added!")
        else:
            st.sidebar.error(f"File must contain the columns: {', '.join(required_columns)}")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")




# Display tasks
st.header("Tasks List")
tasks_df = get_all_tasks('Tasks')
shifts_df = get_all_tasks('Shifts')
if not tasks_df.empty:
    st.dataframe(tasks_df)
    st.dataframe(shifts_df)
else:
    st.write("No tasks added yet.")

# Button to clear all tasks
if st.button("Clear All Tasks"):
    clear_all_tasks()
    st.success("All tasks have been cleared!")

# Calendar view
st.header("Task Calendar")

# def create_calendar(tasks_df):
#     if tasks_df.empty:
#         st.write("No tasks to display in the calendar.")
#         return
    
#     tasks_df["Start"] = pd.to_datetime(tasks_df["Day"] + " " + tasks_df["StartTime"])
#     tasks_df["End"] = tasks_df["Start"] + pd.to_timedelta(tasks_df["Duration"])
    
#     chart = alt.Chart(tasks_df).mark_bar().encode(
#         x=alt.X('Start:T', title="Start Time"),
#         x2='End:T',
#         y=alt.Y('Day:N', title="Day of the Week", sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
#         color=alt.Color('TaskName:N', title="Task Name"),
#         tooltip=['TaskName', 'Start', 'End', 'Day']
#     ).properties(
#         title="Task Calendar with Days of the Week",
#         width=800,
#         height=500
#     )
    
#     st.altair_chart(chart, use_container_width=True)

# if tasks:
#     create_calendar(pd.DataFrame(tasks))
# else:
#     st.write("No tasks available to display in the calendar.")

if not tasks_df.empty:
    st.download_button(
        label="Download Tasks as CSV",
        data=tasks_df.to_csv(index=False).encode("utf-8"),
        file_name="tasks.csv",
        mime="text/csv"
    )