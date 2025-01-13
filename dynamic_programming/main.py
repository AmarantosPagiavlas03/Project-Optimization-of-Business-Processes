import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

# Function to display tasks in a calendar format with days of the week
def create_calendar(tasks_df):
    if tasks_df.empty:
        st.write("No tasks to display in the calendar.")
        return
    
    # Calculate necessary columns for visualization
    tasks_df["End DateTime"] = tasks_df["Start Date"] + tasks_df["Start Time"] + tasks_df["Duration"]
    tasks_df["Start"] = (tasks_df["Start Date"] + tasks_df["Start Time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    tasks_df["End"] = tasks_df["End DateTime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    tasks_df["Day of Week"] = (tasks_df["Start Date"]).dt.strftime("%A")  # Get day name
    
    # Create Altair chart
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

# Streamlit app
st.title("Task Scheduler")

# Sidebar for form input
st.sidebar.header("Add Task")

# Initialize session state for start_time and tasks if not already set
if "start_time" not in st.session_state:
    st.session_state["start_time"] = datetime.now().time()
if "tasks" not in st.session_state:
    st.session_state["tasks"] = []

task_name = st.sidebar.text_input("Task Name", "")
start_date = st.sidebar.date_input("Start Date", value=datetime.now().date())

# Use session state to store start_time
start_time = st.sidebar.time_input(
    "Start Time",
    value=st.session_state["start_time"],
    key="start_time_widget",
)

# Update session state when the time is changed
st.session_state["start_time"] = start_time

duration_hours = st.sidebar.number_input("Duration Hours", min_value=0, max_value=23, value=1)
duration_minutes = st.sidebar.number_input("Duration Minutes", min_value=0, max_value=59, value=0)

# Debugging collected inputs
st.write("Selected time:", start_time)
st.write("Selected datetime:", start_date)
st.write("Duration Hours:", duration_hours, "Duration Minutes:", duration_minutes)

# Button to add task
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

# File uploader for Excel input
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])
if uploaded_file:
    try:
        # Read the uploaded file
        uploaded_tasks = pd.read_excel(uploaded_file)
        # Ensure necessary columns are present
        required_columns = {"Task Name", "Start Date", "Start Time", "Duration"}
        if required_columns.issubset(uploaded_tasks.columns):
            for _, row in uploaded_tasks.iterrows():
                st.session_state["tasks"].append(
                    {
                        "Task Name": row["Task Name"],
                        "Start Date": pd.Timestamp(row["Start Date"]),
                        "Start Time": pd.to_timedelta(row["Start Time"]),
                        "Duration": pd.to_timedelta(row["Duration"]),
                    }
                )
            st.sidebar.success("Tasks from the uploaded file have been added!")
        else:
            st.sidebar.error(f"File must contain the columns: {', '.join(required_columns)}")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

# Main section for displaying tasks
st.header("Tasks List")

# Button to clear the DataFrame
if st.button("Clear All Tasks"):
    st.session_state["tasks"] = []
    st.success("All tasks have been cleared!")

if st.session_state["tasks"]:
    tasks_df = pd.DataFrame(st.session_state["tasks"])
    st.dataframe(tasks_df)
else:
    st.write("No tasks added yet.")

# Calendar view
st.header("Task Calendar")
if st.session_state["tasks"]:
    tasks_df = pd.DataFrame(st.session_state["tasks"])
    create_calendar(tasks_df)
