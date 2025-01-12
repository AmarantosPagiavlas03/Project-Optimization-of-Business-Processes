import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

# Function to display tasks in a calendar format using Altair
def create_calendar(tasks_df):
    if tasks_df.empty:
        st.write("No tasks to display in the calendar.")
        return
    
    tasks_df["End DateTime"] = tasks_df["Start Date"] + tasks_df["Start Time"] + tasks_df["Duration"]
    tasks_df["Start"] = (tasks_df["Start Date"] + tasks_df["Start Time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    tasks_df["End"] = tasks_df["End DateTime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    chart = alt.Chart(tasks_df).mark_bar().encode(
        x=alt.X('Start:T', title="Start Time"),
        x2='End:T',
        y=alt.Y('Task Name:N', title="Task Name", sort='-x'),
        color=alt.Color('Task Name:N', legend=None)
    ).properties(
        title="Task Calendar",
        width=700,
        height=400
    )
    
    st.altair_chart(chart, use_container_width=True)

# Streamlit app
st.title("Task Scheduler")

# Sidebar for form input
st.sidebar.header("Add Task")
task_name = st.sidebar.text_input("Task Name", "")
start_date = st.sidebar.date_input("Start Date", value=datetime.now().date())
start_time = st.sidebar.time_input("Start Time", value=datetime.now().time())
duration_hours = st.sidebar.number_input("Duration Hours", min_value=0, max_value=23, value=1)
duration_minutes = st.sidebar.number_input("Duration Minutes", min_value=0, max_value=59, value=0)

# Debugging collected inputs
st.write("Selected time:", start_time)
st.write("Selected datetime:", start_date)
st.write("Duration Hours:", duration_hours, "Duration Minutes:", duration_minutes)

# Button to add task
if "tasks" not in st.session_state:
    st.session_state["tasks"] = []

if st.sidebar.button("Add Task"):
    if task_name:
        duration = timedelta(hours=duration_hours, minutes=duration_minutes)
        st.session_state["tasks"].append(
            {
                "Task Name": task_name,
                "Start Date": pd.Timestamp(start_date),
                "Start Time": timedelta(hours=start_time.hour, minutes=start_time.minute),
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
    st.dataframe(tasks_df)
else:
    st.write("No tasks added yet.")

# Calendar view
st.header("Task Calendar")
if st.session_state["tasks"]:
    tasks_df = pd.DataFrame(st.session_state["tasks"])
    tasks_df["End DateTime"] = tasks_df["Start Date"] + tasks_df["Start Time"] + tasks_df["Duration"]
    create_calendar(tasks_df)
