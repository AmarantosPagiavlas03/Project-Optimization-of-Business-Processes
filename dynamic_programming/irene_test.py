import pandas as pd
import random
from datetime import timedelta, datetime

# Sample data for task names, durations, and nurses required
task_names = ["Admin Check", "Patient Round", "Blood Test", "Medication Dispense"]
nurses_required = [1, 2, 3, 4]

# Days of the week including Saturday and Sunday
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Function to generate random times in 24-hour format between 00:00 and 24:00
def generate_random_time():
    start_hour = random.randint(0, 23)  # Start time between 00:00 and 23:59
    start_minute = random.choice([0, 30])
    start_time = datetime.strptime(f"{start_hour}:{start_minute}", "%H:%M")
    end_time = start_time + timedelta(minutes=random.choice([30, 60]))  # Add 30 or 60 minutes
    return start_time.strftime("%H:%M"), end_time.strftime("%H:%M")

# Function to generate valid durations (randomly less than the time difference)
def generate_valid_duration(start_time, end_time):
    # Convert to datetime objects
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")
    diff_minutes = (end - start).seconds // 60  # duration in minutes

    # Generate a random duration less than the time difference
    if diff_minutes > 1:
        return f"{random.randint(1, diff_minutes - 1)} minutes"
    else:
        return "1 minute"  # Minimum duration if the difference is too small

# Generate data for 100 rows
data = []
for _ in range(100):
    task_id = f"T{random.randint(100, 999)}"
    task_name = random.choice(task_names)
    day = random.choice(days)
    start_time, end_time = generate_random_time()
    duration = generate_valid_duration(start_time, end_time)
    nurses = random.choice(nurses_required)
    repeats = random.randint(1, 2)

    data.append([task_id, task_name, day, start_time, end_time, duration, nurses, repeats])

# Create a DataFrame
df = pd.DataFrame(data, columns=["Task ID", "Task Name", "Day", "Start Time", "End Time", "Duration", "Nurses Required", "Repeats (per day)"])

# Save to Excel
file_path = '/mnt/data/task_schedule_full_day.xlsx'
df.to_excel(file_path, index=False)

file_path
