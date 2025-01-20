import pandas as pd
import random
import datetime

shift_ids = range(1, 101)  # 100 shifts
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

shifts_data = []
for shift_id in shift_ids:
    start_hour = random.randint(0, 24)
    end_hour = (start_hour + random.randint(4, 12)) % 24  # Shifts are 4-12 hours long
    start_time = datetime.time(start_hour, random.choice([0, 15, 30, 45, 60]))
    end_time = datetime.time(end_hour, random.choice([0, 15, 30, 45, 60]))
    break_time = datetime.time((start_hour + 2) % 24, random.choice([0, 15, 30, 45, 60]))  # Break starts 2 hours after start
    break_duration = datetime.timedelta(minutes=random.choice([15, 30, 60]))  # 15-60 minutes break

    shifts_data.append({
        "id": shift_id,
        "StartTime": start_time.strftime("%H:%M:%S"),
        "EndTime": end_time.strftime("%H:%M:%S"),
        "BreakTime": break_time.strftime("%H:%M:%S"),
        "BreakDuration": str(break_duration),
        "Weight": round(random.choice([0.5, 1.0, 1.5, 2.0])),
        **{day: random.randint(0, 1) for day in days},  # Randomly assign active days
        "Flexibility": random.choice(["Low", "Moderate", "High"]),
        "Notes": f"Generated shift {shift_id}"
    })
# Define function to assign weights
def assign_weight(shifts_data):
    if start_timedatetime.time(6, 0) <= shifts_data < datetime.time(14, 0):  # Morning shift
        return 1.0
    elif datetime.time(14, 0) <= shifts_data < datetime.time(22, 0):  # Afternoon shift
        return 1.5
    else:  # Night shift
        return 2.0

shifts_df = pd.DataFrame(shifts_data)

shifts_df.to_excel("large_shifts.xlsx", index=False)

print("File 'large_shifts.xlsx' has been generated successfully!")