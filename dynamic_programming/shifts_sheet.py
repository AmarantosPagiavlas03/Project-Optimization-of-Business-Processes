import pandas as pd
import random
import datetime

# Generate shifts data
shift_ids = range(1, 101)  # 100 shifts
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

shifts_data = []
for shift_id in shift_ids:
    start_hour = random.randint(0, 23)
    end_hour = (start_hour + random.randint(4, 12)) % 24  # Shifts are 4-12 hours long
    start_time = datetime.time(start_hour, random.choice([0, 15, 30, 45]))
    end_time = datetime.time(end_hour, random.choice([0, 15, 30, 45]))
    
    # Calculate shift length (in hours)
    shift_length = ((end_hour - start_hour) + 24) % 24 + (end_time.minute - start_time.minute) / 60

    # Adjust break duration: if shift is more than 8 hours, break is 1 hour
    if shift_length > 8:
        break_duration_minutes = 60  # 1 hour break
    else:
        break_duration_minutes = 30 

    break_duration = datetime.timedelta(minutes=break_duration_minutes)
    break_time_hour = (start_hour + 2) % 24  # Break starts 2 hours after the shift starts
    break_time = datetime.time(break_time_hour, random.choice([0, 15, 30, 45]))


    shifts_data.append({
        "id": shift_id,
        "StartTime": start_time.strftime("%H:%M:%S"),
        "EndTime": end_time.strftime("%H:%M:%S"),
        "BreakTime": break_time.strftime("%H:%M:%S"),
        "BreakDuration": str(break_duration),
        "ShiftLength": round(shift_length, 2),  # Rounded to 2 decimal places
        **{day: random.randint(0, 1) for day in days},  # Randomly assign active days
        "Flexibility": random.choice(["Low", "Moderate", "High"]),
    })

# Define function to assign weights
def assign_weight(row):
    start_time = datetime.datetime.strptime(row["StartTime"], "%H:%M:%S").time()
    end_time = datetime.datetime.strptime(row["EndTime"], "%H:%M:%S").time()

    if datetime.time(6, 0) <= start_time < datetime.time(14, 0):  # Morning shift
        return 1.0
    elif datetime.time(14, 0) <= start_time < datetime.time(22, 0):  # Afternoon shift
        return 1.5
    else:  # Night shift
        return 2.0

# Convert to DataFrame
shifts_data = pd.DataFrame(shifts_data)

# Apply the function to assign weights
shifts_data["Weight"] = shifts_data.apply(assign_weight, axis=1)

# Save to Excel
shifts_data.to_excel("shifts_sheet.xlsx", index=False)

print("File 'shifts_sheet.ts.xlsx' has been generated successfully!")
