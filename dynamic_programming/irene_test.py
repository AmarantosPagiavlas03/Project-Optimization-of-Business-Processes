import pandas as pd
import random
from datetime import timedelta, datetime

print(12)
# Sample data for task names, durations, and nurses required
task_names = ["Admin Check", "Patient Round", "Blood Test", "Medication Dispense"]
nurses_required = [1, 2, 3, 4]

# Days of the week
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


# Function to generate random times
def generate_random_time():
    start_hour = random.randint(8, 12)
    start_minute = random.choice([0, 30])
    start_time = datetime.strptime(f"{start_hour}:{start_minute}", "%H:%M")
    end_time = start_time + timedelta(minutes=random.choice([30, 60]))
    return start_time.strftime("%H:%M"), end_time.strftime("%H:%M")


# Function to generate valid durations (strictly less than time difference)
def generate_valid_duration(start_time, end_time):
    # Convert to datetime objects
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")
    diff = (end - start).seconds / 60  # duration in minutes

    # Ensure duration is less than the time difference
    if diff > 60:
        return "59 minutes"
    elif diff > 30:
        return "30 minutes"
    else:
        return "15 minutes"


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
df = pd.DataFrame(data, columns=["Task ID", "Task Name", "Day", "Start Time", "End Time", "Duration", "Nurses Required",
                                 "Repeats (per day)"])

# Save to Excel
file_path = '/mnt/data/task_schedule_strict_duration.xlsx'
df.to_excel(file_path, index=False)

file_path
