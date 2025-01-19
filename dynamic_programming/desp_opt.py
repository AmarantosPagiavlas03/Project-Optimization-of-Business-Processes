import pandas as pd
from pulp import LpProblem, LpVariable, lpSum, LpMinimize, LpBinary

# Load the tasks and shifts data from Excel files
tasks_path = 'nursing_tasks_schedule.xlsx'
shifts_path = 'large_shifts.xlsx'

tasks_data = pd.ExcelFile(tasks_path).parse(0)
shifts_data = pd.ExcelFile(shifts_path).parse(0)

# Convert time columns to datetime.time for accurate comparison
tasks_data['Start Window'] = pd.to_datetime(tasks_data['Start Window'], format='%H:%M').dt.time
tasks_data['End Window'] = pd.to_datetime(tasks_data['End Window'], format='%H:%M').dt.time
shifts_data['StartTime'] = pd.to_datetime(shifts_data['StartTime'], format='%H:%M:%S').dt.time
shifts_data['EndTime'] = pd.to_datetime(shifts_data['EndTime'], format='%H:%M:%S').dt.time
shifts_data['BreakTime'] = pd.to_datetime(shifts_data['BreakTime'], format='%H:%M:%S').dt.time
shifts_data['BreakDuration'] = pd.to_timedelta(shifts_data['BreakDuration'])

# Create the linear programming problem
model = LpProblem("Shift_Scheduling", LpMinimize)

# Decision variables: x[task_id][shift_id] = 1 if task_id is assigned to shift_id
x = {}
for task_id, task_row in tasks_data.iterrows():
    x[task_id] = {}
    for shift_id, shift_row in shifts_data.iterrows():
        x[task_id][shift_id] = LpVariable(f"x_{task_id}_{shift_id}", cat=LpBinary)

# Objective function: Minimize total cost
model += lpSum(shift_row['Weight'] * x[task_id][shift_id]
               for task_id, task_row in tasks_data.iterrows()
               for shift_id, shift_row in shifts_data.iterrows())

# Constraints: Ensure all tasks are covered by the required number of nurses
for task_id, task_row in tasks_data.iterrows():
    task_day = task_row['Day']
    task_start = task_row['Start Window']
    task_end = task_row['End Window']
    nurses_required = task_row['Nurses Required']

    # Find valid shifts for the task
    valid_shifts = []
    for shift_id, shift_row in shifts_data.iterrows():
        if shift_row[task_day] == 1:  # Shift active on the task's day
            shift_start = shift_row['StartTime']
            shift_end = shift_row['EndTime']
            break_start = shift_row['BreakTime']
            break_end = (pd.to_datetime(break_start, format='%H:%M:%S') + shift_row['BreakDuration']).time()

            # Check if the task fits in the shift, avoiding break time
            if (shift_start <= task_start <= break_start and shift_start <= task_end <= break_start) or \
               (break_end <= task_start <= shift_end and break_end <= task_end <= shift_end):
                valid_shifts.append(shift_id)

    # Add constraint to ensure the task is covered by the required number of nurses
    model += lpSum(x[task_id][shift_id] for shift_id in valid_shifts) >= nurses_required

# Solve the linear programming problem
model.solve()

# Extract results: Assign tasks to shifts
matching_shifts_column = []
shift_weights_column = []

for task_id, task_row in tasks_data.iterrows():
    matching_shifts = []
    shift_weights = []
    for shift_id, shift_row in shifts_data.iterrows():
        if x[task_id][shift_id].varValue == 1:  # If this shift is used for this task
            matching_shifts.append(shift_row['id'])
            shift_weights.append(shift_row['Weight'])

    # Save the matching shifts and weights
    matching_shifts_column.append(matching_shifts)
    shift_weights_column.append(shift_weights)

# Add the matching shifts and weights to the tasks data
tasks_data['Matching Shifts'] = matching_shifts_column
tasks_data['Shift Weights'] = shift_weights_column

# Save the updated tasks file
output_path = 'tasks_with_matching_shifts_and_weights_optimized9.xlsx'
tasks_data.to_excel(output_path, index=False)

print(f"Optimized file saved to {output_path}")
