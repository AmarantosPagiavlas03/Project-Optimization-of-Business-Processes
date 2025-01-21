#create a tasks file
import pandas as pd
import random
from datetime import timedelta, datetime

# Define constants
tasks = ["Dressing Change", "Medication Administration", "Physical Therapy", "Wound Care", "Vital Signs Monitoring"]
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
durations = [15, 30, 45, 60]
nurses_required_range = range(1, 6)
start_times = [datetime.strptime(f"{hour}:{minute:02d}", "%H:%M") 
               for hour in range(0, 23) for minute in range(0, 60, 30)]

# Generate random data
data = []
for _ in range(100):
    task = random.choice(tasks)
    day = random.choice(days)
    start_time = random.choice(start_times)
    end_window_length = random.choice(range(30, 181, 30))  # 30 minutes to 3 hours, multiples of 30
    end_time = start_time + timedelta(minutes=end_window_length)
    duration = random.choice([d for d in durations if d <= end_window_length])  # Duration <= end window
    nurses_required = random.choice(nurses_required_range)

    data.append({
        "Task Name": task,
        "Day": day,
        "Start Window": start_time.strftime("%H:%M"),
        "End Window": end_time.strftime("%H:%M"),
        "Duration of Task (mins)": duration,
        "Nurses Required": nurses_required
    })

# Create DataFrame and save to Excel
df = pd.DataFrame(data)
df.to_excel("Nursing_Tasks_Schedule2.xlsx", index=False)

print("File 'Nursing_Tasks_Schedule2.xlsx' has been generated successfully!")