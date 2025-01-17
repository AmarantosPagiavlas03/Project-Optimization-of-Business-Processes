import pandas as pd

#csv to xls file
# Load the CSV file
csv_file = "shifts.csv"  # Replace with your CSV file name
data = pd.read_csv(csv_file)

# Save it as an Excel file
xlsx_file = "tasks4_converted.xlsx"  # Specify the output file name
data.to_excel(xlsx_file, index=False)

print(f"File converted successfully: {xlsx_file}") #dokimase tora ksana


#
import pandas as pd
from pulp import LpProblem, LpVariable, LpMinimize, lpSum
shifts = pd.read_excel("tasks_converted.xlsx")
tasks = pd.read_excel("tasks2_converted.xlsx")

# Load shifts and tasks
shifts = pd.read_excel("tasks_converted.xlsx")
tasks = pd.read_excel("tasks2_converted.xlsx")

# Print the first few rows to check the data
print("Shifts Data:")
print(shifts.head())

print("Tasks Data:")
print(tasks.head())

# Initialize the optimization problem
problem = LpProblem("Task_Shift_Optimization", LpMinimize)

# Create decision variables
task_shift_vars = {}
for task_idx, task in tasks.iterrows():
    for shift_idx, shift in shifts.iterrows():
        # Create a binary variable for each task-shift assignment
        var_name = f"Assign_Task_{task_idx}_to_Shift_{shift_idx}"
        task_shift_vars[(task_idx, shift_idx)] = LpVariable(var_name, cat="Binary")

# Objective: Minimize total shift weights
problem += lpSum(
    task_shift_vars[(task_idx, shift_idx)] * shifts.loc[shift_idx, "Weight"]
    for task_idx, shift_idx in task_shift_vars
)

# Constraint 1: Each task must be assigned to at least one shift
for task_idx, task in tasks.iterrows():
    problem += lpSum(
        task_shift_vars[(task_idx, shift_idx)]
        for shift_idx in shifts.index if (task_idx, shift_idx) in task_shift_vars
    ) >= 1, f"Task_{task_idx}_Assignment"

# Constraint 2: Shifts must not exceed their nurse capacity
for shift_idx, shift in shifts.iterrows():
    problem += lpSum(
        task_shift_vars[(task_idx, shift_idx)] * tasks.loc[task_idx, "NursesRequired"]
        for task_idx in tasks.index if (task_idx, shift_idx) in task_shift_vars
    ) <= shifts.loc[shift_idx, "Capacity"], f"Shift_{shift_idx}_Capacity"

# Constraint 3: Task times must overlap with shift times
for task_idx, task in tasks.iterrows():
    for shift_idx, shift in shifts.iterrows():
        if (task_idx, shift_idx) in task_shift_vars:
            if not (
                pd.to_datetime(shift["StartTime"]) <= pd.to_datetime(task["StartTime"])
                and pd.to_datetime(shift["EndTime"]) >= pd.to_datetime(task["EndTime"])
            ):
                # Prevent assignment if times don't overlap
                problem += task_shift_vars[(task_idx, shift_idx)] == 0

# Solve the optimization problem
problem.solve()

# Collect results
results = []
for (task_idx, shift_idx), var in task_shift_vars.items():
    if var.value() == 1:
        results.append({
            "TaskName": tasks.loc[task_idx, "TaskName"],
            "ShiftID": shift_idx,
            "ShiftStart": shifts.loc[shift_idx, "StartTime"],
            "ShiftEnd": shifts.loc[shift_idx, "EndTime"]
        })

# Convert results to a DataFrame
results_df = pd.DataFrame(results)

# Display the results
print("Optimal Task-Shift Assignment:")
print(results_df)

# Save results to Excel
results_df.to_excel("optimized_schedule.xlsx", index=False)
print("Optimized schedule saved as 'optimized_schedule.xlsx'")

import plotly.express as px

# Visualize task assignments as a Gantt chart
results_df["Start"] = pd.to_datetime(results_df["ShiftStart"])
results_df["End"] = pd.to_datetime(results_df["ShiftEnd"])
fig = px.timeline(
    results_df, 
    x_start="Start", 
    x_end="End", 
    y="TaskName", 
    title="Task-Shift Assignment"
)
fig.show()
