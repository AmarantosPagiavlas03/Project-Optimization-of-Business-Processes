import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import random
import plotly.express as px
from gurobipy import Model, GRB, quicksum
from datetime import time
import io  
import base64
import os
import datetime as dt

DB_FILE = "tasksv2.db"

# ------------------------------------------------------------------
#                           Database
# ------------------------------------------------------------------
def init_db():
    """Initialize the database with necessary tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Table: Tasks
    c.execute('''
        CREATE TABLE IF NOT EXISTS TasksTable2 (
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
    CREATE TABLE IF NOT EXISTS ShiftsTable5 (
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
        INSERT INTO TasksTable2 (TaskName, Day, StartTime, EndTime, Duration, NursesRequired)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (TaskName, Day, StartTime, EndTime, Duration, NursesRequired))
    conn.commit()
    conn.close()

def add_shift_to_db(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO ShiftsTable5 (
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
    intervals.append(time(0, 0))
    return intervals

def get_default_indices_for_intervals(intervals):
    now_plus_1h = (dt.datetime.now() + dt.timedelta(hours=1)).time()
    now_plus_2h = (dt.datetime.now() + dt.timedelta(hours=2)).time()

    nearest_15_1h = (now_plus_1h.minute // 15) * 15
    default_time_1h = now_plus_1h.replace(minute=nearest_15_1h, second=0, microsecond=0)
    nearest_15_2h = (now_plus_2h.minute // 15) * 15
    default_time_2h = now_plus_2h.replace(minute=nearest_15_2h, second=0, microsecond=0)

    default_idx_1h = intervals.index(default_time_1h) if default_time_1h in intervals else 0
    default_idx_2h = intervals.index(default_time_2h) if default_time_2h in intervals else 0
    return default_idx_1h, default_idx_2h

def task_input_form():
    with st.form("task_form", border=False):
        st.subheader("Add New Task")
        intervals = generate_time_intervals()
        default_idx_1h, default_idx_2h = get_default_indices_for_intervals(intervals)

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            TaskName = st.text_input("Task Name", key="task_name")
        with col2:
            Day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        with col3:
            StartTime = st.selectbox("Start", options=intervals, index=default_idx_1h, format_func=lambda t: t.strftime("%H:%M"))
        with col4:
            EndTime = st.selectbox("End", options=intervals, index=default_idx_2h, format_func=lambda t: t.strftime("%H:%M"))
        with col5:
            NursesRequired = st.number_input("Nurses", min_value=1, value=1)

        if st.form_submit_button("➕ Add Task", use_container_width=True):
            if TaskName:
                duration = datetime.combine(datetime.min, EndTime) - datetime.combine(datetime.min, StartTime)
                add_task_to_db(
                    TaskName, Day,
                    f"{StartTime.hour}:{StartTime.minute:02}:00",
                    f"{EndTime.hour}:{EndTime.minute:02}:00",
                    str(duration), NursesRequired
                )
                st.success(f"Task '{TaskName}' added!")
            else:
                st.error("Task name required!")

def shift_input_form():
    with st.form("shift_form", border=False):
        st.subheader("Add New Shift")
        intervals = generate_time_intervals()
        default_idx_1h, default_idx_2h = get_default_indices_for_intervals(intervals)

        cols = st.columns(5)
        with cols[0]:
            Shift_Start = st.selectbox("Shift Start", options=intervals, index=default_idx_1h, format_func=lambda t: t.strftime("%H:%M"))
        with cols[1]:
            Shift_End = st.selectbox("Shift End", options=intervals, index=default_idx_2h, format_func=lambda t: t.strftime("%H:%M"))
        with cols[2]:
            Break_Start = st.selectbox("Break Start", options=intervals, format_func=lambda t: t.strftime("%H:%M"))
        with cols[3]:
            Break_Dur = st.number_input("Break Mins", min_value=15, max_value=120, step=15, value=30)
        with cols[4]:
            Weight = st.number_input("Weight", min_value=0.1, value=1.0, step=0.1)

        st.write("Active Days:")
        days = st.columns(7)
        day_cols = {day: days[i].checkbox(day[:3], value=(i < 5)) for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])}

        if st.form_submit_button("➕ Add Shift", use_container_width=True):
            shift_data = (
                f"{Shift_Start.hour}:{Shift_Start.minute:02}:00",
                f"{Shift_End.hour}:{Shift_End.minute:02}:00",
                f"{Break_Start.hour}:{Break_Start.minute:02}:00",
                str(timedelta(minutes=Break_Dur)),
                Weight,
                *(1 if day_cols[day] else 0 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            )
            add_shift_to_db(shift_data)
            st.success("Shift added!")


# Add these functions after the shift_input_form function
# ------------------------------------------------------------------
#                     Upload Functions
# ------------------------------------------------------------------
def task_template_download():
    template_df = pd.DataFrame({
        "TaskName": ["Morning Rounds", "Medication"],
        "Day": ["Monday", "Tuesday"],
        "StartTime": ["08:00:00", "14:00:00"],
        "EndTime": ["10:00:00", "16:00:00"],
        "Duration": ["2:00:00", "2:00:00"],
        "NursesRequired": [3, 2]
    })
    with st.expander("📁 Task Template"):
        st.download_button(
            label="Download Task Template",
            data=template_df.to_csv(index=False),
            file_name="tasks_template.csv",
            mime="text/csv"
        )

def shift_template_download():
    template_df = pd.DataFrame({
        "StartTime": ["07:00:00", "19:00:00"],
        "EndTime": ["15:00:00", "07:00:00"],
        "BreakTime": ["12:00:00", "02:00:00"],
        "BreakDuration": ["0:30:00", "1:00:00"],
        "Weight": [1.0, 1.5],
        "Monday": [1, 1],
        "Tuesday": [1, 0],
        "Wednesday": [1, 0],
        "Thursday": [1, 0],
        "Friday": [1, 0],
        "Saturday": [0, 1],
        "Sunday": [0, 1]
    })
    with st.expander("📁 Shift Template"):
        st.download_button(
            label="Download Shift Template",
            data=template_df.to_csv(index=False),
            file_name="shifts_template.csv",
            mime="text/csv"
        )

def upload_tasks_excel():
    uploaded_file = st.file_uploader("Upload Tasks", type=["csv", "xlsx"], key="task_upload")
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            required_cols = {"TaskName", "Day", "StartTime", "EndTime", "Duration", "NursesRequired"}
            if not required_cols.issubset(df.columns):
                st.error(f"Missing columns: {required_cols - set(df.columns)}")
                return
                
            for _, row in df.iterrows():
                add_task_to_db(
                    row["TaskName"], row["Day"],
                    row["StartTime"], row["EndTime"],
                    row["Duration"], row["NursesRequired"]
                )
            st.success(f"Successfully uploaded {len(df)} tasks!")
        except Exception as e:
            st.error(f"Error: {str(e)}")

def upload_shifts_excel():
    uploaded_file = st.file_uploadizer("Upload Shifts", type=["csv", "xlsx"], key="shift_upload")
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            required_cols = {"StartTime", "EndTime", "BreakTime", "BreakDuration", "Weight",
                            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
            if not required_cols.issubset(df.columns):
                st.error(f"Missing columns: {required_cols - set(df.columns)}")
                return
            
            for _, row in df.iterrows():
                shift_data = (
                    row["StartTime"], row["EndTime"],
                    row["BreakTime"], row["BreakDuration"],
                    row["Weight"],
                    row["Monday"], row["Tuesday"], row["Wednesday"],
                    row["Thursday"], row["Friday"], row["Saturday"], row["Sunday"]
                )
                add_shift_to_db(shift_data)
            st.success(f"Successfully uploaded {len(df)} shifts!")
        except Exception as e:
            st.error(f"Error: {str(e)}")



# ------------------------------------------------------------------
#                         Optimization
# ------------------------------------------------------------------
def optimize_tasks_with_gurobi():
    tasks_df = get_all("TasksTable2")
    shifts_df = get_all("ShiftsTable5")

    if tasks_df.empty or shifts_df.empty:
        st.error("Add tasks and shifts first!")
        return

    tasks_df["StartTime"] = pd.to_datetime(tasks_df["StartTime"], format="%H:%M:%S").dt.time
    tasks_df["EndTime"] = pd.to_datetime(tasks_df["EndTime"], format="%H:%M:%S").dt.time
    shifts_df["StartTime"] = pd.to_datetime(shifts_df["StartTime"], format="%H:%M:%S").dt.time
    shifts_df["EndTime"] = pd.to_datetime(shifts_df["EndTime"], format="%H:%M:%S").dt.time

    model = Model("Task_Assignment")
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    shift_worker_vars = {}
    for shift_id, shift_row in shifts_df.iterrows():
        for day in day_names:
            if shift_row[day] == 1:
                shift_worker_vars[(shift_id, day)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"Workers_{shift_id}_{day}")

    task_shift_vars = {}
    for task_id, task_row in tasks_df.iterrows():
        t_day = task_row["Day"]
        t_start = task_row["StartTime"]
        t_end = task_row["EndTime"]

        for shift_id, shift_row in shifts_df.iterrows():
            if shift_row[t_day] == 1:
                shift_start = shift_row["StartTime"]
                shift_end = shift_row["EndTime"]
                if shift_start <= t_start and shift_end >= t_end:
                    task_shift_vars[(task_id, shift_id, t_day)] = model.addVar(vtype=GRB.BINARY, name=f"Task_{task_id}_Shift_{shift_id}")

    model.setObjective(
        quicksum(shift_worker_vars[(s, d)] * shifts_df.loc[s, "Weight"] for (s, d) in shift_worker_vars),
        GRB.MINIMIZE
    )

    for task_id in tasks_df.index:
        feasible = [task_shift_vars[key] for key in task_shift_vars if key[0] == task_id]
        if feasible:
            model.addConstr(quicksum(feasible) >= 1)

    for (s_id, day) in shift_worker_vars:
        model.addConstr(
            quicksum(tasks_df.loc[t_id, "NursesRequired"] * task_shift_vars[(t_id, s_id, day)]
                    for (t_id, s, d) in task_shift_vars if s == s_id and d == day) <= shift_worker_vars[(s_id, day)]
        )

    with st.spinner("Optimizing..."):
        model.optimize()

    if model.status == GRB.OPTIMAL:
        results = []
        for (t_id, s_id, d), var in task_shift_vars.items():
            if var.x > 0.5:
                workers = shift_worker_vars.get((s_id, d), 0).x
                results.append({
                    "Task": tasks_df.loc[t_id, "TaskName"],
                    "Shift": shifts_df.loc[s_id, "id"],
                    "Day": d,
                    "Start": tasks_df.loc[t_id, "StartTime"].strftime("%H:%M"),
                    "End": tasks_df.loc[t_id, "EndTime"].strftime("%H:%M"),
                    "Nurses": workers
                })

        results_df = pd.DataFrame(results)
        if not results_df.empty:
            st.success("Optimization Complete!")
            st.dataframe(results_df, use_container_width=True)
            st.download_button("📥 Download Results", results_df.to_csv(), "assignments.csv")
        else:
            st.warning("No valid assignments found")
    else:
        st.error("Optimization failed")

# ------------------------------------------------------------------
#                         Visualization
# ------------------------------------------------------------------
def display_timeline():
    st.subheader("Schedule Timeline")
    
    tasks = get_all("TasksTable2")
    shifts = get_all("ShiftsTable5")
    
    if not tasks.empty:
        tasks["Start"] = pd.to_datetime("2023-01-01 " + tasks["StartTime"])
        tasks["End"] = pd.to_datetime("2023-01-01 " + tasks["EndTime"])
        fig_tasks = px.timeline(tasks, x_start="Start", x_end="End", y="Day", color="TaskName",
                              title="Tasks Schedule", labels={"TaskName": "Task"})
        st.plotly_chart(fig_tasks, use_container_width=True)
    
    if not shifts.empty:
        shifts["Start"] = pd.to_datetime("2023-01-01 " + shifts["StartTime"])
        shifts["End"] = pd.to_datetime("2023-01-01 " + shifts["EndTime"])
        fig_shifts = px.timeline(shifts, x_start="Start", x_end="End", y=shifts.index, color="id",
                               title="Shifts Schedule", labels={"id": "Shift ID"})
        st.plotly_chart(fig_shifts, use_container_width=True)

# ------------------------------------------------------------------
#                         Main App
# ------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Hospital Scheduler", layout="wide", page_icon="🏥")
    st.markdown("""
    <style>
        .st-emotion-cache-1y4p8pa {padding: 2rem 1rem 10rem;}
        .st-emotion-cache-1v0mbdj {border-radius: 10px;}
        .stPlotlyChart {border: 1px solid #e6e6e6; border-radius: 10px; padding: 20px;}
        .stDataFrame {border-radius: 10px;}
        div[data-testid="stExpander"] {background: #fafafa; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)
    
    init_db()
    
    st.title("🏥 Hospital Staff Scheduler")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📥 Data Input", "📊 Schedule View", "⚙️ Optimization"])
    
    # Update the input_tab section to include upload functionality
    with tab1:
        st.subheader("Data Input Methods")
        manual_tab, upload_tab = st.tabs(["✍️ Manual Entry", "📤 Bulk Upload"])
        
        with manual_tab:
            with st.expander("➕ Add New Task", expanded=True):
                task_input_form()
            
            with st.expander("👥 Add New Shift", expanded=True):
                shift_input_form()
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧹 Clear All Tasks", use_container_width=True, type="secondary"):
                    clear_all("TasksTable2")
                    st.success("All tasks cleared!")
            with col2:
                if st.button("🧹 Clear All Shifts", use_container_width=True, type="secondary"):
                    clear_all("ShiftsTable5")
                    st.success("All shifts cleared!")

        with upload_tab:
            st.subheader("Bulk Data Upload")
            up_col1, up_col2 = st.columns(2)
            
            with up_col1:
                st.markdown("### Tasks Upload")
                upload_tasks_excel()
                task_template_download()
            
            with up_col2:
                st.markdown("### Shifts Upload")
                upload_shifts_excel()
                shift_template_download()
    
    with tab2:
        display_timeline()
        col_stats1, col_stats2 = st.columns(2)
        with col_stats1:
            st.metric("Total Tasks", len(get_all("TasksTable2")))
        with col_stats2:
            st.metric("Total Shifts", len(get_all("ShiftsTable5")))
    
    with tab3:
        st.subheader("Task-Shift Optimization")
        if st.button("🚀 Start Optimization", type="primary", use_container_width=True):
            optimize_tasks_with_gurobi()

if __name__ == "__main__":
    main()