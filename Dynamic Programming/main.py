import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Function to display tasks in a calendar format
def create_calendar(tasks_df):
    if tasks_df.empty:
        st.write("No tasks to display in the calendar.")
        return
    tasks_df["End DateTime"] = tasks_df["Start DateTime"] + tasks_df["Duration"]
    fig = px.timeline(
        tasks_df,
        x_start="Start DateTime",
        x_end="End DateTime",
        y="Task Name",
        title="Task Calendar",
        labels={"Task Name": "Task"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig, use_container_width=True)

# Streamlit app
st.title("Task Scheduler")

# Sidebar for form input
st.sidebar.header("Add Task")
task_name = st.sidebar.text_input("Task Name", "")
start_date = st.sidebar.date_input("Start Date", value=datetime.now().date())
start_time = st.sidebar.time_input("Start Time", value=datetime.now().time())
duration_hours = st.sidebar.number_input("Duration Hours", min_value=0, max_value=23, value=1)
duration_minutes = st.sidebar.number_input("Duration Minutes", min_value=0, max_value=59, value=0)

# Button to add task
if "tasks" not in st.session_state:
    st.session_state["tasks"] = []

if st.sidebar.button("Add Task"):
    if task_name:
        start_datetime = datetime.combine(start_date, start_time)
        duration = timedelta(hours=duration_hours, minutes=duration_minutes)
        st.session_state["tasks"].append(
            {
                "Task Name": task_name,
                "Start DateTime": start_datetime,
                "Duration": duration,
            }
        )
        st.sidebar.success(f"Task '{task_name}' added!")
    else:
        st.sidebar.error("Task name cannot be empty!")

# Main section for displaying tasks
st.header("Tasks List")
if st.session_state["tasks"]:
    tasks_df = pd.DataFrame(st.session_state["tasks"])
    tasks_df["Start DateTime"] = pd.to_datetime(tasks_df["Start DateTime"])
    tasks_df["Duration"] = tasks_df["Duration"].apply(lambda x: str(x))
    st.dataframe(tasks_df)
else:
    st.write("No tasks added yet.")

# Calendar view
st.header("Task Calendar")
if st.session_state["tasks"]:
    tasks_df = pd.DataFrame(st.session_state["tasks"])
    tasks_df["Start DateTime"] = pd.to_datetime(tasks_df["Start DateTime"])
    tasks_df["Duration"] = tasks_df["Duration"].apply(lambda x: pd.Timedelta(x))
    create_calendar(tasks_df)
