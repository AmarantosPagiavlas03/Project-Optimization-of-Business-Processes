import pandas as pd

# Load the data from Excel files
tasks_path = 'nursing_tasks_schedule.xlsx'
shifts_path = 'shifts.xlsx'

tasks_data = pd.ExcelFile(tasks_path).parse(0)
shifts_data = pd.ExcelFile(shifts_path).parse(0)

# Convert time columns to datetime.time for accurate comparison
tasks_data['Start Window'] = pd.to_datetime(tasks_data['Start Window'], format='%H:%M').dt.time
tasks_data['End Window'] = pd.to_datetime(tasks_data['End Window'], format='%H:%M').dt.time
shifts_data['StartTime'] = pd.to_datetime(shifts_data['StartTime'], format='%H:%M:%S').dt.time
shifts_data['EndTime'] = pd.to_datetime(shifts_data['EndTime'], format='%H:%M:%S').dt.time

# Function to match tasks to shifts
def match_task_to_shifts(task_row, shifts_df):
    task_day = task_row['Day']
    task_start = task_row['Start Window']
    task_end = task_row['End Window']
    
    matching_shifts = []
    
    for _, shift_row in shifts_df.iterrows():
        # Check if the shift matches the task's day and time window
        if (shift_row[task_day] == 1 and  # Shift is active on the task's day
            shift_row['StartTime'] <= task_start <= shift_row['EndTime'] and  # Task starts within shift
            shift_row['StartTime'] <= task_end <= shift_row['EndTime']):  # Task ends within shift
            matching_shifts.append(shift_row['id'])
    
    return matching_shifts

# Apply the matching function to each task
tasks_data['Matching Shifts'] = tasks_data.apply(lambda row: match_task_to_shifts(row, shifts_data), axis=1)

# Save the output to an Excel file for review
output_path = 'tasks_with_matching_shifts.xlsx'
tasks_data.to_excel(output_path, index=False)

# Print the first few rows of the updated tasks_data for reference
print(tasks_data.head())
print(f"\nOutput saved to: {output_path}")

import pandas as pd

# Load the data from Excel files
tasks_path = 'nursing_tasks_schedule.xlsx'
shifts_path = 'shifts.xlsx'

tasks_data = pd.ExcelFile(tasks_path).parse(0)
shifts_data = pd.ExcelFile(shifts_path).parse(0)

# Convert time columns to datetime for processing
tasks_data['Start Window'] = pd.to_datetime(tasks_data['Start Window'], format='%H:%M').dt.time
tasks_data['End Window'] = pd.to_datetime(tasks_data['End Window'], format='%H:%M').dt.time
shifts_data['StartTime'] = pd.to_datetime(shifts_data['StartTime'], format='%H:%M:%S').dt.time
shifts_data['EndTime'] = pd.to_datetime(shifts_data['EndTime'], format='%H:%M:%S').dt.time

# Compute weights for shifts based on duration
shifts_data['Duration_Hours'] = (pd.to_datetime(shifts_data['EndTime'], format='%H:%M:%S') - 
                                 pd.to_datetime(shifts_data['StartTime'], format='%H:%M:%S')).dt.total_seconds() / 3600
shifts_data['Weight'] = pd.to_numeric(shifts_data['Duration_Hours'])  # Base weight proportional to duration

# Function to match tasks to shifts with weights included
def match_task_to_shifts(task_row, shifts_df):
    task_day = task_row['Day']
    task_start = task_row['Start Window']
    task_end = task_row['End Window']
    
    matching_shifts = []
    matching_weights = []
    
    for _, shift_row in shifts_df.iterrows():
        if (shift_row[task_day] == 1 and  # Shift is active on the task's day
            shift_row['StartTime'] <= task_start <= shift_row['EndTime'] and  # Task starts within shift
            shift_row['StartTime'] <= task_end <= shift_row['EndTime']):  # Task ends within shift
            matching_shifts.append(shift_row['id'])
            matching_weights.append(shift_row['Weight'])
    
    return matching_shifts, matching_weights

# Apply the matching function to each task
tasks_data[['Matching Shifts', 'Shift Weights']] = tasks_data.apply(
    lambda row: pd.Series(match_task_to_shifts(row, shifts_data)), axis=1
)

# Save the combined tasks data with matching shifts and weights
output_path = 'tasks_with_matching_shifts_and_weights_separated.xlsx'
tasks_data.to_excel(output_path, index=False)

# Print the first few rows of the updated tasks data
print(tasks_data.head())
print(f"\nTasks with matching shifts and weights saved to: {output_path}")


#now optimize
from pulp import LpProblem, LpVariable, lpSum, LpMinimize, LpBinary
import pandas as pd

# Load matched tasks data
tasks_path = 'tasks_with_matching_shifts2.xlsx'
tasks_data = pd.ExcelFile(tasks_path).parse(0)

# Parse Matching Shifts into lists
tasks_data['Matching Shifts'] = tasks_data['Matching Shifts'].apply(lambda x: eval(x) if isinstance(x, str) else [])

# Define the optimization problem
model = LpProblem("Nursing_Ward_Scheduling", LpMinimize)

# Decision variables: x[task, shift] = 1 if task is assigned to shift, 0 otherwise
task_shift_vars = {}
for index, task_row in tasks_data.iterrows():
    task_shift_vars[index] = {}
    for shift in task_row['Matching Shifts']:
        task_shift_vars[index][shift] = LpVariable(f"task_{index}_shift_{shift}", cat=LpBinary)

# Objective: Minimize total cost
model += lpSum(
    task_shift_vars[task_id][shift] * shifts_data.loc[shifts_data['id'] == shift, 'Weight'].values[0]
    for task_id, shifts in task_shift_vars.items()
    for shift in shifts
)

# Constraint 1: Each task must be assigned to exactly one shift
for task_id, shifts in task_shift_vars.items():
    model += lpSum(shifts.values()) == 1

# Solve the model
model.solve()

# Extract and combine data for the optimized schedule
optimized_schedule = []

for task_id, shifts in task_shift_vars.items():
    for shift, var in shifts.items():
        if var.varValue == 1:  # Check if the shift is assigned
            task_row = tasks_data.iloc[task_id]
            shift_row = shifts_data.loc[shifts_data['id'] == shift].iloc[0]
            optimized_schedule.append({
                'Task Name': task_row['Task Name'],
                'Day': task_row['Day'],
                'Start Window': task_row['Start Window'],
                'End Window': task_row['End Window'],
                'Assigned Shift ID': shift,
                'Shift Start': shift_row['StartTime'],
                'Shift End': shift_row['EndTime'],
                'Cost': shift_row['Weight']
            })

# Convert to DataFrame and save
optimized_schedule_df = pd.DataFrame(optimized_schedule)
output_path = 'optimized_schedule_final.xlsx'
optimized_schedule_df.to_excel(output_path, index=False)

# Print the first few rows of the optimized schedule
print(optimized_schedule_df.head())
print(f"\nOptimized schedule saved to: {output_path}")