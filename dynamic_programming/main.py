import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import altair as alt

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
        CREATE TABLE if not exists shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            StartTime TEXT NOT NULL,
            EndTime TEXT,
            NursesRequired INTEGER NOT NULL,
            Duration TEXT NOT NULL
        )
        ''')
        conn.commit()
    finally:
        if conn:
            conn.close()

def add_task_to_db(TaskName,Day, StartTime,EndTime, Duration,NursesRequired):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO Tasks (TaskName, Day, StartTime,EndTime, Duration, NursesRequired) VALUES (?, ?, ?, ? , ?,?)",
              (TaskName,Day, StartTime,EndTime, Duration,NursesRequired))
    conn.commit()
    conn.close()

def get_all_tasks():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM Tasks")
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
tasks_df = get_all_tasks()
if not tasks_df.empty:
    st.dataframe(tasks_df)
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