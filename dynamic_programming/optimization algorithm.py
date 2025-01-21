#optimization algorithm
import pandas as pd
from datetime import timedelta

nurse_file = "shifts_sheet.xlsx"
nurse_data = pd.read_excel(nurse_file, sheet_name= "Sheet1")

#process the data
availability = {}
for _, row in nurse_data.iterrows():
    nurse_id = row["ID"]
    start_time = pd.to_datetime(row["Start Time"]).time()
    end_time = pd.to_datetime(row["End Time"]).time()
    break_time = pd.to_datetime(row["Break Time"], errors="coerce").time() if pd.notna(row["Break Time"]) else None
    break_duration = int(row["Break Duration"])
    shift_length = int(row["Shift Length"])

    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        if row[day] == 1:
            # Store availability information
            availability[(nurse_id, day)] = {
                "start_time": start_time,
                "end_time": end_time,
                "break_time": break_time,
                "break_duration": break_duration,
                "shift_length": shift_length
            }

# Display processed availability
for (nurse_id, day), details in availability.items():
    print(f"Nurse {nurse_id} - {day}:")
    print(f"  Available from {details['start_time']} to {details['end_time']}")
    print(f"  Shift Length: {details['shift_length']} hours")
    if details["break_time"]:
        print(f"  Break Time: {details['break_time']} ({details['break_duration']} minutes)")
    print()