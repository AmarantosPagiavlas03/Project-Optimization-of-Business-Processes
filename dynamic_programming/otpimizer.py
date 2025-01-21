import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum

def optimize_nurse_schedule(tasks, shifts):
    """
    Optimize the nurse schedule based on tasks and shifts.

    Args:
        tasks (pd.DataFrame): DataFrame with columns ['Task Name', 'Start Time', 'End Time', 'Nurses Required'].
        shifts (pd.DataFrame): DataFrame with columns ['Shift Name', 'Start Time', 'End Time', 'Max Nurses', 'Cost'].

    Returns:
        dict: Solution containing optimal shifts and nurse assignments.
    """
    # Create the linear programming problem
    problem = LpProblem("Nurse_Schedule_Optimization", LpMinimize)

    # Convert times to minutes for easier calculations
    tasks['Start Time'] = pd.to_datetime(tasks['Start Time']).dt.time
    tasks['End Time'] = pd.to_datetime(tasks['End Time']).dt.time

    shifts['Start Time'] = pd.to_datetime(shifts['Start Time']).dt.time
    shifts['End Time'] = pd.to_datetime(shifts['End Time']).dt.time

    # Decision variables for each shift
    shift_vars = {row['Shift Name']: LpVariable(row['Shift Name'], cat='Binary') for _, row in shifts.iterrows()}

    # Objective function: minimize total cost
    problem += lpSum(shift_vars[shift['Shift Name']] * shift['Cost'] for _, shift in shifts.iterrows())

    # Constraints: tasks must be covered by shifts
    for _, task in tasks.iterrows():
        task_start = task['Start Time']
        task_end = task['End Time']
        nurses_required = task['Nurses Required']

        # Calculate overlap of shifts with the task
        overlapping_shifts = shifts[
            (shifts['Start Time'] <= task_start) & (shifts['End Time'] >= task_end)
        ]

        # Constraint to ensure enough nurses for the task
        problem += lpSum(
            shift_vars[shift['Shift Name']] * shift['Max Nurses'] for _, shift in overlapping_shifts.iterrows()
        ) >= nurses_required

    # Solve the problem
    problem.solve()

    # Collect results
    results = {
        'Shift Name': [],
        'Selected': [],
        'Cost': [],
    }

    for _, shift in shifts.iterrows():
        results['Shift Name'].append(shift['Shift Name'])
        results['Selected'].append(shift_vars[shift['Shift Name']].value())
        results['Cost'].append(shift['Cost'] if shift_vars[shift['Shift Name']].value() else 0)

    return pd.DataFrame(results)
