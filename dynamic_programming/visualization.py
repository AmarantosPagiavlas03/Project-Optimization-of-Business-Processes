import streamlit as st
import pandas as pd
from dynamic_programming.database import get_all

# ------------------------------------------------------------------
#                          Visualization
# ------------------------------------------------------------------
def display_tasks_and_shifts():
    """Display tasks and shifts as Gantt charts for the week."""
    st.header("Visualize Tasks and Shifts for the Week")

    tasks_df = get_all("TasksTable2")
    shifts_df = get_all("ShiftsTable5")

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

 