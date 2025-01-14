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
        # Create the tasks table
        c.execute('''
        CREATE TABLE if not exists tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration TEXT NOT NULL
            nurses_required INTEGER NOT NULL,
        )
        ''')
        conn.commit()
        # Create the shifts table
        c.execute('''
        CREATE TABLE if not exists shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            nurses_required INTEGER NOT NULL,
            duration TEXT NOT NULL
        )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

def add_task_to_db(task_name,day, start_time,end_time, duration,nurses_required):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (task_name, day, start_time,end_time, duration, nurses_required) VALUES (?, ?, ?, ? , ?)",
              (task_name,day, start_time,end_time, duration,nurses_required))
    conn.commit()
    conn.close()

def get_all_tasks():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT task_name, day, start_time, end_time, duration, nurses_required FROM tasks")
    rows = c.fetchall()
    conn.close()
    tasks = []
    for row in rows:
        tasks.append({
            "Task Name": row['task_name'],
            "Start Time": pd.to_timedelta(row['start_time']),
            "Duration": pd.to_timedelta(row['duration']),
            "End Time": pd.to_timedelta(row['end_time']),
            "Nurses Required": row['nurses_required'],
        })
    return tasks

def clear_all_tasks():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Streamlit app
st.title("Task Scheduler with SQLite Persistence")

# Sidebar for adding tasks
st.sidebar.header("Add Task")

task_name = st.sidebar.text_input("Task Name", "")
day = st.sidebar.text_input("Day of the Week", "")
start_time = st.sidebar.time_input("Start Time", value=datetime.now().time())
end_time = st.sidebar.time_input("End Time", value=datetime.now().time())
duration_hours = st.sidebar.number_input("Duration Hours", min_value=0, max_value=23, value=1)
duration_minutes = st.sidebar.number_input("Duration Minutes", min_value=0, max_value=59, value=0)
nurses_required = st.sidebar.number_input("Nurses Required", min_value=1, value=1)

# Add task button
if st.sidebar.button("Add Task"):
    if task_name:
        duration = timedelta(hours=duration_hours, minutes=duration_minutes)
        add_task_to_db(
            task_name,
            day,
            f"{start_time.hour}:{start_time.minute}:00",
            f"{end_time.hour}:{end_time.minute}:00",
            f"{duration}",
            f"{nurses_required}"
        )
        st.sidebar.success(f"Task '{task_name}' added!")
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
tasks = get_all_tasks()
if tasks:
    tasks_df = pd.DataFrame(tasks)
    st.dataframe(tasks_df)
else:
    st.write("No tasks added yet.")

# Button to clear all tasks
if st.button("Clear All Tasks"):
    clear_all_tasks()
    st.success("All tasks have been cleared!")

# Calendar view
st.header("Task Calendar")

def create_calendar(tasks_df):
    if tasks_df.empty:
        st.write("No tasks to display in the calendar.")
        return
    
    tasks_df["End DateTime"] = tasks_df["Start Date"] + tasks_df["Start Time"] + tasks_df["Duration"]
    tasks_df["Start"] = (tasks_df["Start Date"] + tasks_df["Start Time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    tasks_df["End"] = tasks_df["End DateTime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    tasks_df["Day of Week"] = (tasks_df["Start Date"]).dt.strftime("%A")  # Get day name
    
    chart = alt.Chart(tasks_df).mark_bar().encode(
        x=alt.X('Start:T', title="Start Time"),
        x2='End:T',
        y=alt.Y('Day of Week:N', title="Day of the Week", sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
        color=alt.Color('Task Name:N', title="Task Name"),
        tooltip=['Task Name', 'Start', 'End', 'Day of Week']
    ).properties(
        title="Task Calendar with Days of the Week",
        width=800,
        height=500
    )
    
    st.altair_chart(chart, use_container_width=True)

if tasks:
    create_calendar(pd.DataFrame(tasks))
else:
    st.write("No tasks available to display in the calendar.")

if tasks:
    st.download_button(
        label="Download Tasks as CSV",
        data=tasks_df.to_csv(index=False).encode("utf-8"),
        file_name="tasks.csv",
        mime="text/csv"
    )