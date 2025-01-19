# Input data
tasks = [
    {"name": "Task 1", "start_window": 9 * 60, "end_window": 23 * 60, "duration": 30, "nurses_required": 5},
    {"name": "Task 2", "start_window": 9 * 60, "end_window": 23 * 60, "duration": 120, "nurses_required": 7},
    {"name": "Task 3", "start_window": 9 * 60, "end_window": 23 * 60, "duration": 30, "nurses_required": 1},
    {"name": "Task 4", "start_window": 9 * 60, "end_window": 23 * 60, "duration": 30, "nurses_required": 6},
    {"name": "Task 5", "start_window": 9 * 60, "end_window": 23 * 60, "duration": 30, "nurses_required": 3},
    {"name": "Task 6", "start_window": 9 * 60, "end_window": 23 * 60, "duration": 30, "nurses_required": 2},
    {"name": "Task 7", "start_window": 13 * 60, "end_window": 23 * 60, "duration": 30, "nurses_required": 2},
]

# Sort tasks by 'nurses_required' in descending order
tasks = sorted(tasks, key=lambda x: x["nurses_required"], reverse=True)

# Dynamic shifts
shifts = [
    {"start": 0 * 60, "end": 12 * 60, "cost": 10},  # Shift 2: 08:00-16:00
    {"start": 12 * 60, "end": 24 * 60, "cost": 20}, # Shift 3: 16:00-24:00
]

# Initialize schedule and cost tracker
schedule = []
time_slots = {i: 0 for i in range(24 * 60)}  # Tracks maximum nurses at each minute

# Helper function to calculate the total cost for all shifts
def calculate_shift_cost(temp_time_slots):
    shift_costs = []
    for shift in shifts:
        max_nurses = max(temp_time_slots[t] for t in range(shift["start"], shift["end"]))
        shift_costs.append(max_nurses * shift["cost"])
    return sum(shift_costs)

# Task assignment logic
for task in tasks:
    best_cost = float("inf")
    best_start = None

    # Check all valid start times within the task's time window
    for start_time in range(task["start_window"], task["end_window"] - task["duration"] + 1):
        end_time = start_time + task["duration"]

        # Temporarily update time_slots to test the assignment
        temp_time_slots = time_slots.copy()
        for t in range(start_time, end_time):
            temp_time_slots[t] += task["nurses_required"]

        # Calculate the cost for this potential assignment
        cost = calculate_shift_cost(temp_time_slots)

        # Update if this interval is better
        if cost < best_cost:
            best_cost = cost
            best_start = start_time

    # Assign the task to the best interval
    if best_start is not None:
        end_time = best_start + task["duration"]
        schedule.append({
            "task": task["name"],
            "start": best_start,
            "end": end_time,
            "nurses_required": task["nurses_required"],
        })

        # Update time slots with the assigned task
        for t in range(best_start, end_time):
            time_slots[t] += task["nurses_required"]

# Calculate final shift costs
shift_costs = []
for shift in shifts:
    max_nurses = max(time_slots[t] for t in range(shift["start"], shift["end"]))
    shift_costs.append(max_nurses * shift["cost"])

# Output the schedule and costs
for assignment in schedule:
    start_hour, start_minute = divmod(assignment["start"], 60)
    end_hour, end_minute = divmod(assignment["end"], 60)
    print(f"{assignment['task']} assigned from {start_hour:02}:{start_minute:02} to {end_hour:02}:{end_minute:02}")

total_cost = sum(shift_costs)
print(f"Shift costs: {shift_costs}")
print(f"Total cost: {total_cost}")