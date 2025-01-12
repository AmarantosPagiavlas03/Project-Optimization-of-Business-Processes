import pandas as pd
from datetime import timedelta

class TaskScheduler:
    def __init__(self, tasks):
        """
        Initialize with a DataFrame of tasks.
        Each task should have: start_window, end_window, duration, and nurses_required.
        """
        self.tasks = tasks
        self.schedule = None

    def generate_schedule(self):
        """
        Generate a schedule by assigning tasks to 15-minute intervals.
        """
        schedule = []
        for _, task in self.tasks.iterrows():
            start_window = pd.to_datetime(task["start_window"])
            end_window = pd.to_datetime(task["end_window"])
            duration = timedelta(minutes=task["duration"])
            nurses = task["nurses_required"]

            current_time = start_window
            while current_time + duration <= end_window:
                schedule.append({
                    "start_time": current_time,
                    "end_time": current_time + duration,
                    "nurses_required": nurses,
                })
                current_time += timedelta(minutes=15)
        self.schedule = pd.DataFrame(schedule)
        return self.schedule

import pandas as pd

class ShiftOptimizer:
    def __init__(self, shifts, schedule):
        """
        Initialize with shift options and the generated schedule.
        Shifts should include cost and availability data.
        """
        self.shifts = shifts
        self.schedule = schedule
        self.optimized_shifts = None

    def optimize_shifts(self):
        """
        Optimize shifts to minimize costs while covering all tasks.
        """
        optimized_shifts = []
        # Placeholder logic: match shifts to tasks.
        for _, task in self.schedule.iterrows():
            suitable_shifts = self.shifts[
                (self.shifts["start_time"] <= task["start_time"]) &
                (self.shifts["end_time"] >= task["end_time"])
            ]
            if not suitable_shifts.empty:
                best_shift = suitable_shifts.iloc[0]  # Placeholder: pick the first option
                optimized_shifts.append(best_shift)
        self.optimized_shifts = pd.DataFrame(optimized_shifts).drop_duplicates()
        return self.optimized_shifts

import matplotlib.pyplot as plt

def visualize_schedule(schedule):
    """
    Visualize the generated schedule as a Gantt chart.
    """
    fig, ax = plt.subplots()
    for i, task in schedule.iterrows():
        ax.barh(
            task["nurses_required"], 
            (task["end_time"] - task["start_time"]).seconds / 60,
            left=task["start_time"].hour + task["start_time"].minute / 60,
            label=f"Task {i}"
        )
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Nurses")
    plt.show()

import pandas as pd

def read_excel(file_path):
    """
    Read Excel file with tasks or shifts data.
    """
    return pd.read_excel(file_path)

def write_excel(dataframe, file_path):
    """
    Write a DataFrame to an Excel file.
    """
    dataframe.to_excel(file_path, index=False)


def main():
    # Load tasks and shifts data
    tasks = read_excel("tasks.xlsx")
    shifts = read_excel("shifts.xlsx")

    # Generate schedule
    scheduler = TaskScheduler(tasks)
    schedule = scheduler.generate_schedule()

    # Optimize shifts
    optimizer = ShiftOptimizer(shifts, schedule)
    optimized_shifts = optimizer.optimize_shifts()

    # Save results
    write_excel(schedule, "schedule.xlsx")
    write_excel(optimized_shifts, "optimized_shifts.xlsx")

    # Visualize schedule
    visualize_schedule(schedule)

if __name__ == "__main__":
    main()