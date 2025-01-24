import pandas as pd
import sqlite3
# import streamlit as st
DB_FILE = "tasksv2.db"


# ------------------------------------------------------------------
#                           Database
# ------------------------------------------------------------------
def init_db():
    """
    Initialize the database with necessary tables.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Table: Tasks
    c.execute('''
        CREATE TABLE IF NOT EXISTS TasksTable2 (
            id INTEGER PRIMARY KEY,
            TaskName TEXT NOT NULL,
            Day TEXT NOT NULL,
            StartTime TEXT NOT NULL,
            EndTime TEXT NOT NULL,
            Duration TEXT NOT NULL,
            NursesRequired INTEGER NOT NULL
        )
    ''')

    # Table: Shifts
    c.execute('''
    CREATE TABLE IF NOT EXISTS ShiftsTable5 (
        id INTEGER PRIMARY KEY,
        StartTime TEXT NOT NULL,
        EndTime TEXT NOT NULL,
        BreakTime TEXT NOT NULL,
        BreakDuration TEXT NOT NULL,
        Weight FLOAT NOT NULL,

        Monday INT NOT NULL,
        Tuesday INT NOT NULL,
        Wednesday INT NOT NULL,
        Thursday INT NOT NULL,
        Friday INT NOT NULL,
        Saturday INT NOT NULL,
        Sunday INT NOT NULL,

        -- Add day-specific columns for needed workers
        MondayNeeded INT DEFAULT 0,
        TuesdayNeeded INT DEFAULT 0,
        WednesdayNeeded INT DEFAULT 0,
        ThursdayNeeded INT DEFAULT 0,
        FridayNeeded INT DEFAULT 0,
        SaturdayNeeded INT DEFAULT 0,
        SundayNeeded INT DEFAULT 0
    );
    ''')

    # Table: Workers
    c.execute('''
        CREATE TABLE IF NOT EXISTS Workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            WorkerName TEXT NOT NULL,
            MondayStart TEXT,
            MondayEnd TEXT,
            TuesdayStart TEXT,
            TuesdayEnd TEXT,
            WednesdayStart TEXT,
            WednesdayEnd TEXT,
            ThursdayStart TEXT,
            ThursdayEnd TEXT,
            FridayStart TEXT,
            FridayEnd TEXT,
            SaturdayStart TEXT,
            SaturdayEnd TEXT,
            SundayStart TEXT,
            SundayEnd TEXT
        )
    ''')

    conn.commit()
    conn.close()


# -------------------------- DB Helpers ---------------------------
def add_task_to_db(TaskName, Day, StartTime, EndTime, Duration, NursesRequired):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO TasksTable2 (TaskName, Day, StartTime, EndTime, Duration, NursesRequired)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (TaskName, Day, StartTime, EndTime, Duration, NursesRequired))
    conn.commit()
    conn.close()


def add_shift_to_db(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO ShiftsTable5 (
            StartTime, EndTime, BreakTime, BreakDuration, Weight,
            Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()


def add_worker_to_db(
    worker_name,
    mon_start, mon_end,
    tue_start, tue_end,
    wed_start, wed_end,
    thu_start, thu_end,
    fri_start, fri_end,
    sat_start, sat_end,
    sun_start, sun_end
):
    """
    Insert a new worker into the Workers table.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO Workers (
            WorkerName,
            MondayStart, MondayEnd,
            TuesdayStart, TuesdayEnd,
            WednesdayStart, WednesdayEnd,
            ThursdayStart, ThursdayEnd,
            FridayStart, FridayEnd,
            SaturdayStart, SaturdayEnd,
            SundayStart, SundayEnd
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        worker_name,
        mon_start, mon_end,
        tue_start, tue_end,
        wed_start, wed_end,
        thu_start, thu_end,
        fri_start, fri_end,
        sat_start, sat_end,
        sun_start, sun_end
    ))
    conn.commit()
    conn.close()


def get_all(table):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df


def clear_all(table):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()

# def update_needed_workers_for_each_day(results_df):
#     """
#     Use the first-optimization assignments (results_df) to populate
#     MondayNeeded, TuesdayNeeded, ... columns for each ShiftID in ShiftsTable5.
#     """
#     if results_df.empty:
#         st.error("No results to update needed workers. `results_df` is empty.")
#         return
#     print("Columns in results_df:", results_df.columns)

#     required_columns = ["ShiftID", "TaskDay", "WorkersNeededForShift"]
#     missing_columns = [col for col in required_columns if col not in results_df.columns]
#     if missing_columns:
#         st.error(f"Missing required columns in results_df: {missing_columns}")
#         return
    
#     # 1. Aggregate how many workers are needed for each (ShiftID, Day).
#     #    If a single shift has multiple tasks on the same day, you might 
#     #    want sum() or max(). That depends on your logic. Let's use max() here.
#     shift_day_needs = (
#         results_df
#         .groupby(["ShiftID", "TaskDay"])["WorkersNeededForShift"]
#         .max()  # or .sum()
#         .reset_index()
#     )
#     # 2. Build a dictionary: shift_day_dict[shift_id][day] = needed count
#     day_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
#     shift_day_dict = {}

#     for _, row in shift_day_needs.iterrows():
#         sid = row["ShiftID"]
#         day = row["TaskDay"]         # e.g. "Monday"
#         needed = int(row["WorkersNeededForShift"])

#         if sid not in shift_day_dict:
#             shift_day_dict[sid] = {d: 0 for d in day_list}  # default 0 for each day

#         # Assign the needed count for that day
#         shift_day_dict[sid][day] = needed
 
#     # 3. Update ShiftsTable5 for each shift ID
#     conn = sqlite3.connect(DB_FILE)
#     c = conn.cursor()

#     for sid, day_map in shift_day_dict.items():
#         c.execute('''
#             UPDATE ShiftsTable5
#             SET
#               MondayNeeded    = :mon,
#               TuesdayNeeded   = :tue,
#               WednesdayNeeded = :wed,
#               ThursdayNeeded  = :thu,
#               FridayNeeded    = :fri,
#               SaturdayNeeded  = :sat,
#               SundayNeeded    = :sun
#             WHERE id = :shift_id
#         ''', {
#             "mon": day_map["Monday"],
#             "tue": day_map["Tuesday"],
#             "wed": day_map["Wednesday"],
#             "thu": day_map["Thursday"],
#             "fri": day_map["Friday"],
#             "sat": day_map["Saturday"],
#             "sun": day_map["Sunday"],
#             "shift_id": sid
#         })

#     conn.commit()
#     conn.close()

#     st.success("Day-specific NeededWorkers columns have been updated in ShiftsTable5!")

# ------------------------------------------------------------------
#                        Example Data Inserts
# ------------------------------------------------------------------
def insert():
    """
    Insert a small example data set into Tasks and Shifts.
    (For demonstration)
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO TasksTable2 (
            TaskName,
            Day,
            StartTime,
            EndTime,
            Duration,
            NursesRequired
        )
        VALUES
            ('Dressing Change', 'Monday', '07:30:00', '07:45:00', 15, 1),
            ('Vital Signs Monitoring', 'Monday', '10:30:00', '11:00:00', 30, 2),
            ('Wound Care', 'Monday', '14:30:00', '15:15:00', 45, 3),
            ('Medication Administration', 'Monday', '22:00:00', '22:30:00', 30, 2),
            ('Physical Therapy', 'Tuesday', '08:00:00', '08:45:00', 45, 2),
            ('Dressing Change', 'Tuesday', '13:30:00', '13:45:00', 15, 1),
            ('Vital Signs Monitoring', 'Tuesday', '16:00:00', '16:30:00', 30, 2),
            ('Medication Administration', 'Tuesday', '21:30:00', '22:00:00', 30, 2),
            ('Wound Care', 'Wednesday', '07:30:00', '08:15:00', 45, 3),
            ('Physical Therapy', 'Wednesday', '12:00:00', '12:45:00', 45, 2),
            ('Dressing Change', 'Wednesday', '18:00:00', '18:15:00', 15, 1),
            ('Vital Signs Monitoring', 'Thursday', '09:00:00', '09:30:00', 30, 2),
            ('Medication Administration', 'Thursday', '13:00:00', '13:30:00', 30, 2),
            ('Wound Care', 'Thursday', '17:30:00', '18:15:00', 45, 3),
            ('Dressing Change', 'Friday', '07:30:00', '07:45:00', 15, 1),
            ('Vital Signs Monitoring', 'Friday', '14:30:00', '15:00:00', 30, 2),
            ('Medication Administration', 'Friday', '21:30:00', '22:00:00', 30, 2),
            ('Wound Care', 'Saturday', '09:30:00', '10:15:00', 45, 3),
            ('Physical Therapy', 'Saturday', '14:00:00', '14:45:00', 45, 2),
            ('Vital Signs Monitoring', 'Saturday', '20:00:00', '20:30:00', 30, 2),
            ('Dressing Change', 'Sunday', '14:30:00', '14:45:00', 15, 1),
            ('Wound Care', 'Sunday', '20:00:00', '20:45:00', 45, 3);
    ''')
    conn.commit()
    c.execute('''
        INSERT INTO ShiftsTable5 (
            StartTime,
            EndTime,
            BreakTime,
            BreakDuration,
            Weight,
            Monday,
            Tuesday,
            Wednesday,
            Thursday,
            Friday,
            Saturday,
            Sunday
        )
        VALUES
            ('07:00:00', '15:00:00', '11:00:00', '0:30:00', 1200, 1, 1, 1, 1, 1, 0, 0),
            ('15:00:00', '23:00:00', '19:00:00', '0:30:00', 1400, 1, 1, 1, 1, 1, 1, 1),
            ('23:00:00', '07:00:00', '03:00:00', '0:30:00', 1600, 1, 1, 1, 1, 1, 1, 1),
            ('08:00:00', '14:00:00', '12:00:00', '0:20:00', 1000, 1, 1, 1, 1, 1, 0, 0),
            ('14:00:00', '20:00:00', '17:00:00', '0:30:00', 1100, 1, 1, 1, 1, 1, 1, 1),
            ('20:00:00', '02:00:00', '23:00:00', '0:20:00', 1300, 0, 1, 1, 1, 1, 1, 1),
            ('09:00:00', '17:00:00', '13:00:00', '0:45:00', 1500, 1, 1, 0, 1, 1, 0, 0),
            ('06:00:00', '14:00:00', '10:00:00', '0:30:00', 1100, 1, 1, 1, 1, 1, 1, 0),
            ('14:00:00', '22:00:00', '18:00:00', '0:30:00', 1200, 1, 1, 1, 1, 1, 1, 1),
            ('10:00:00', '18:00:00', '13:30:00', '0:30:00', 1300, 1, 1, 1, 1, 1, 0, 0);
    ''')
    conn.commit()
    conn.close()

def insert2():
    """
    Another example data set.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO TasksTable2 (
            TaskName,
            Day,
            StartTime,
            EndTime,
            Duration,
            NursesRequired
        )
        VALUES
        ('Physical Therapy', 'Thursday', '07:00:00', '08:00:00', 45, 2),
        ('Vital Signs Monitoring', 'Friday', '06:00:00', '06:30:00', 30, 5),
        ('Vital Signs Monitoring', 'Wednesday', '05:30:00', '07:00:00', 60, 4),
        ('Medication Administration', 'Monday', '04:00:00', '05:30:00', 45, 1),
        ('Dressing Change', 'Saturday', '08:00:00', '10:00:00', 60, 4),
        ('Wound Care', 'Sunday', '12:30:00', '13:00:00', 15, 3),
        ('Vital Signs Monitoring', 'Thursday', '12:00:00', '13:00:00', 30, 5),
        ('Physical Therapy', 'Wednesday', '20:30:00', '23:30:00', 45, 2),
        ('Vital Signs Monitoring', 'Sunday', '21:30:00', '23:00:00', 30, 1),
        ('Physical Therapy', 'Saturday', '18:00:00', '19:00:00', 30, 5),
        ('Wound Care', 'Saturday', '00:00:00', '02:00:00', 60, 5),
        ('Vital Signs Monitoring', 'Tuesday', '19:30:00', '22:00:00', 30, 4),
        ('Wound Care', 'Monday', '19:00:00', '22:00:00', 15, 3),
        ('Medication Administration', 'Sunday', '11:00:00', '13:00:00', 60, 4),
        ('Physical Therapy', 'Thursday', '13:30:00', '16:30:00', 30, 1),
        ('Wound Care', 'Wednesday', '08:30:00', '10:00:00', 15, 2),
        ('Medication Administration', 'Tuesday', '17:00:00', '19:00:00', 60, 2),
        ('Medication Administration', 'Saturday', '19:30:00', '22:30:00', 30, 4),
        ('Dressing Change', 'Sunday', '15:30:00', '18:30:00', 15, 4),
        ('Vital Signs Monitoring', 'Tuesday', '04:30:00', '06:30:00', 60, 1),
        ('Wound Care', 'Wednesday', '22:00:00', '01:00:00', 30, 4),
        ('Physical Therapy', 'Tuesday', '17:00:00', '18:00:00', 45, 5),
        ('Dressing Change', 'Friday', '20:00:00', '21:30:00', 45, 3),
        ('Physical Therapy', 'Thursday', '02:00:00', '04:00:00', 60, 5),
        ('Dressing Change', 'Saturday', '22:00:00', '22:30:00', 30, 5),
        ('Wound Care', 'Friday', '09:30:00', '11:00:00', 15, 3),
        ('Vital Signs Monitoring', 'Saturday', '00:00:00', '03:00:00', 45, 3),
        ('Medication Administration', 'Monday', '02:30:00', '03:30:00', 30, 4),
        ('Vital Signs Monitoring', 'Monday', '12:30:00', '14:00:00', 30, 3),
        ('Dressing Change', 'Tuesday', '17:00:00', '19:30:00', 30, 5),
        ('Physical Therapy', 'Monday', '07:30:00', '08:00:00', 30, 4),
        ('Dressing Change', 'Wednesday', '17:00:00', '18:00:00', 15, 1),
        ('Physical Therapy', 'Thursday', '16:30:00', '17:00:00', 15, 2),
        ('Wound Care', 'Friday', '00:00:00', '00:30:00', 15, 5),
        ('Dressing Change', 'Friday', '18:30:00', '19:30:00', 45, 4),
        ('Wound Care', 'Sunday', '20:30:00', '23:00:00', 45, 2),
        ('Physical Therapy', 'Saturday', '09:00:00', '11:30:00', 60, 3),
        ('Vital Signs Monitoring', 'Thursday', '14:00:00', '15:00:00', 30, 4),
        ('Physical Therapy', 'Sunday', '13:00:00', '14:30:00', 15, 2),
        ('Dressing Change', 'Monday', '07:00:00', '09:00:00', 30, 3),
        ('Dressing Change', 'Sunday', '09:30:00', '10:00:00', 15, 2),
        ('Vital Signs Monitoring', 'Monday', '12:30:00', '14:30:00', 15, 3),
        ('Wound Care', 'Sunday', '21:00:00', '23:30:00', 15, 1),
        ('Physical Therapy', 'Monday', '21:30:00', '22:30:00', 15, 5),
        ('Medication Administration', 'Sunday', '15:00:00', '17:00:00', 45, 5),
        ('Vital Signs Monitoring', 'Tuesday', '20:00:00', '21:30:00', 45, 2),
        ('Wound Care', 'Monday', '06:30:00', '07:30:00', 15, 5),
        ('Physical Therapy', 'Wednesday', '21:30:00', '23:00:00', 30, 1),
        ('Physical Therapy', 'Friday', '17:30:00', '18:30:00', 60, 1),
        ('Physical Therapy', 'Thursday', '16:00:00', '18:00:00', 30, 5),
        ('Medication Administration', 'Thursday', '00:30:00', '02:00:00', 45, 2),
        ('Vital Signs Monitoring', 'Sunday', '01:00:00', '02:00:00', 60, 2),
        ('Medication Administration', 'Saturday', '14:00:00', '17:00:00', 45, 4),
        ('Physical Therapy', 'Friday', '17:00:00', '20:00:00', 45, 4),
        ('Physical Therapy', 'Sunday', '19:30:00', '20:30:00', 30, 4),
        ('Wound Care', 'Thursday', '01:00:00', '04:00:00', 60, 4),
        ('Wound Care', 'Saturday', '03:00:00', '05:00:00', 30, 5),
        ('Vital Signs Monitoring', 'Tuesday', '08:30:00', '09:30:00', 45, 3),
        ('Wound Care', 'Friday', '15:30:00', '16:00:00', 30, 2),
        ('Physical Therapy', 'Wednesday', '17:00:00', '19:00:00', 30, 3),
        ('Wound Care', 'Thursday', '06:30:00', '09:00:00', 60, 4),
        ('Medication Administration', 'Tuesday', '13:00:00', '15:30:00', 60, 1),
        ('Physical Therapy', 'Friday', '10:30:00', '13:30:00', 60, 5),
        ('Dressing Change', 'Tuesday', '06:00:00', '06:30:00', 15, 3),
        ('Physical Therapy', 'Sunday', '11:00:00', '14:00:00', 45, 2),
        ('Physical Therapy', 'Friday', '12:00:00', '13:30:00', 45, 2),
        ('Vital Signs Monitoring', 'Tuesday', '07:30:00', '10:00:00', 60, 1),
        ('Dressing Change', 'Tuesday', '19:30:00', '20:30:00', 45, 4),
        ('Wound Care', 'Thursday', '17:00:00', '17:30:00', 30, 3),
        ('Dressing Change', 'Sunday', '04:00:00', '06:30:00', 45, 2),
        ('Medication Administration', 'Thursday', '21:00:00', '23:00:00', 60, 3),
        ('Medication Administration', 'Monday', '04:30:00', '07:30:00', 30, 4),
        ('Physical Therapy', 'Friday', '21:00:00', '22:30:00', 45, 3),
        ('Vital Signs Monitoring', 'Wednesday', '13:00:00', '15:00:00', 30, 4),
        ('Wound Care', 'Saturday', '22:30:00', '01:00:00', 45, 1),
        ('Physical Therapy', 'Tuesday', '08:00:00', '09:00:00', 45, 3),
        ('Medication Administration', 'Sunday', '21:30:00', '00:30:00', 15, 3),
        ('Physical Therapy', 'Sunday', '12:00:00', '14:30:00', 60, 3),
        ('Physical Therapy', 'Sunday', '01:00:00', '03:00:00', 60, 3),
        ('Medication Administration', 'Saturday', '13:30:00', '14:30:00', 15, 3),
        ('Medication Administration', 'Tuesday', '18:00:00', '19:00:00', 15, 2),
        ('Physical Therapy', 'Wednesday', '15:00:00', '15:30:00', 30, 2),
        ('Wound Care', 'Sunday', '22:30:00', '01:30:00', 30, 4),
        ('Physical Therapy', 'Friday', '03:30:00', '04:30:00', 15, 4),
        ('Physical Therapy', 'Wednesday', '03:30:00', '04:30:00', 30, 5),
        ('Vital Signs Monitoring', 'Friday', '06:30:00', '07:30:00', 15, 3),
        ('Wound Care', 'Monday', '09:00:00', '10:00:00', 45, 2),
        ('Dressing Change', 'Thursday', '12:30:00', '13:00:00', 30, 2),
        ('Dressing Change', 'Friday', '09:30:00', '11:30:00', 30, 5),
        ('Wound Care', 'Wednesday', '20:30:00', '22:30:00', 60, 3),
        ('Vital Signs Monitoring', 'Saturday', '08:30:00', '09:30:00', 15, 4),
        ('Dressing Change', 'Sunday', '20:00:00', '23:00:00', 30, 1),
        ('Medication Administration', 'Thursday', '08:30:00', '11:00:00', 60, 2),
        ('Vital Signs Monitoring', 'Thursday', '22:30:00', '23:30:00', 30, 3),
        ('Physical Therapy', 'Tuesday', '21:30:00', '23:30:00', 60, 3),
        ('Dressing Change', 'Wednesday', '04:30:00', '05:00:00', 30, 5),
        ('Physical Therapy', 'Thursday', '15:30:00', '17:00:00', 60, 1),
        ('Wound Care', 'Saturday', '21:30:00', '22:30:00', 45, 3),
        ('Medication Administration', 'Saturday', '07:30:00', '09:30:00', 60, 3),
        ('Physical Therapy', 'Friday', '20:30:00', '21:00:00', 15, 1);
    ''')
    conn.commit()
    c.execute('''
        INSERT INTO ShiftsTable5 (
            StartTime,
            EndTime,
            BreakTime,
            BreakDuration,
            Weight,
            Monday,
            Tuesday,
            Wednesday,
            Thursday,
            Friday,
            Saturday,
            Sunday
        )
        VALUES
('06:15:00', '10:30:00', '08:30:00', '0:30:00', 4.25, 0, 1, 0, 0, 1, 0, 1),
('14:15:00', '22:30:00', '16:45:00', '1:00:00', 8.25, 1, 1, 1, 0, 0, 1, 0),
('20:00:00', '07:00:00', '22:00:00', '1:00:00', 11, 0, 1, 0, 1, 1, 0, 0),
('04:00:00', '12:45:00', '06:00:00', '1:00:00', 8.75, 1, 0, 1, 0, 0, 0, 1),
('12:30:00', '22:30:00', '14:30:00', '1:00:00', 10, 0, 0, 0, 0, 1, 0, 0),
('02:00:00', '08:30:00', '04:15:00', '0:30:00', 6.5, 1, 1, 0, 1, 1, 1, 0),
('20:00:00', '00:45:00', '22:00:00', '0:30:00', 4.75, 1, 0, 0, 1, 0, 1, 1),
('15:30:00', '23:15:00', '17:00:00', '0:30:00', 7.75, 0, 1, 0, 1, 0, 0, 1),
('19:15:00', '07:30:00', '21:30:00', '1:00:00', 12.25, 0, 0, 1, 1, 1, 1, 1),
('18:00:00', '23:30:00', '20:15:00', '0:30:00', 5.5, 0, 0, 0, 1, 0, 0, 1),
('05:15:00', '17:30:00', '07:30:00', '1:00:00', 12.25, 1, 1, 0, 0, 1, 1, 1),
('08:30:00', '14:30:00', '10:45:00', '0:30:00', 6, 0, 1, 0, 1, 1, 0, 0),
('19:30:00', '23:00:00', '21:00:00', '0:30:00', 3.5, 1, 0, 0, 0, 1, 0, 0),
('15:15:00', '02:00:00', '17:30:00', '1:00:00', 10.75, 0, 1, 0, 1, 1, 1, 1),
('05:30:00', '17:15:00', '07:30:00', '1:00:00', 11.75, 0, 1, 0, 1, 1, 1, 0),
('18:00:00', '06:15:00', '20:00:00', '1:00:00', 12.25, 0, 1, 1, 1, 0, 1, 0),
('04:45:00', '11:30:00', '06:00:00', '0:30:00', 6.75, 1, 0, 0, 1, 0, 1, 1),
('23:30:00', '11:00:00', '01:45:00', '1:00:00', 11.5, 1, 0, 1, 1, 0, 0, 0),
('23:45:00', '08:00:00', '01:15:00', '1:00:00', 8.25, 0, 1, 0, 1, 1, 0, 1),
('03:30:00', '13:30:00', '05:30:00', '1:00:00', 10, 0, 1, 1, 0, 0, 0, 1),
('14:15:00', '01:30:00', '16:00:00', '1:00:00', 11.25, 1, 1, 1, 0, 1, 1, 0),
('21:00:00', '01:00:00', '23:15:00', '0:30:00', 4, 0, 1, 1, 0, 0, 1, 0),
('10:30:00', '16:15:00', '12:15:00', '0:30:00', 5.75, 0, 1, 1, 1, 1, 0, 0),
('20:45:00', '01:15:00', '22:30:00', '0:30:00', 4.5, 1, 1, 1, 1, 0, 0, 1),
('02:15:00', '13:30:00', '04:30:00', '1:00:00', 11.25, 1, 0, 0, 1, 0, 0, 1),
('08:15:00', '16:45:00', '10:45:00', '1:00:00', 8.5, 0, 0, 0, 0, 0, 0, 0),
('11:15:00', '20:30:00', '13:00:00', '1:00:00', 9.25, 0, 0, 0, 0, 1, 0, 0),
('22:00:00', '04:00:00', '00:30:00', '0:30:00', 6, 1, 1, 0, 0, 1, 1, 0),
('22:00:00', '10:00:00', '00:00:00', '1:00:00', 12, 1, 1, 0, 0, 1, 0, 0),
('09:30:00', '16:45:00', '11:00:00', '0:30:00', 7.25, 0, 0, 0, 0, 1, 1, 1),
('09:15:00', '20:15:00', '11:30:00', '1:00:00', 11, 1, 1, 1, 1, 0, 0, 1),
('04:30:00', '12:45:00', '06:30:00', '1:00:00', 8.25, 0, 1, 1, 1, 1, 0, 1),
('18:30:00', '03:30:00', '20:00:00', '1:00:00', 9, 1, 1, 1, 0, 1, 1, 0),
('16:30:00', '04:00:00', '18:45:00', '1:00:00', 11.5, 0, 0, 0, 1, 1, 0, 1),
('17:30:00', '22:00:00', '19:30:00', '0:30:00', 4.5, 0, 1, 0, 1, 0, 0, 1),
('19:00:00', '05:45:00', '21:00:00', '1:00:00', 10.75, 0, 1, 0, 1, 1, 0, 1),
('21:00:00', '07:00:00', '23:00:00', '1:00:00', 10, 1, 0, 1, 1, 0, 1, 0),
('23:45:00', '09:15:00', '01:15:00', '1:00:00', 9.5, 1, 0, 1, 0, 0, 1, 1),
('21:45:00', '04:45:00', '23:15:00', '0:30:00', 7, 1, 1, 1, 0, 0, 0, 1),
('00:30:00', '09:45:00', '02:00:00', '1:00:00', 9.25, 0, 1, 0, 1, 0, 0, 0),
('23:45:00', '09:30:00', '01:45:00', '1:00:00', 9.75, 0, 1, 1, 0, 1, 0, 1),
('22:15:00', '07:45:00', '00:45:00', '1:00:00', 9.5, 0, 1, 0, 1, 1, 1, 1),
('01:15:00', '06:00:00', '03:00:00', '0:30:00', 4.75, 1, 0, 0, 1, 0, 0, 0),
('17:15:00', '01:30:00', '19:15:00', '1:00:00', 8.25, 0, 1, 1, 1, 1, 0, 1),
('15:00:00', '01:30:00', '17:00:00', '1:00:00', 10.5, 0, 0, 0, 0, 0, 1, 1),
('23:45:00', '03:00:00', '01:30:00', '0:30:00', 3.25, 0, 1, 1, 0, 0, 1, 1),
('22:45:00', '05:15:00', '00:00:00', '0:30:00', 6.5, 0, 0, 1, 1, 0, 1, 0),
('22:15:00', '03:15:00', '00:30:00', '0:30:00', 5, 0, 0, 0, 1, 1, 1, 1),
('17:45:00', '03:30:00', '19:15:00', '1:00:00', 9.75, 1, 0, 1, 0, 1, 0, 1),
('04:15:00', '16:45:00', '06:30:00', '1:00:00', 12.5, 1, 0, 0, 1, 1, 0, 0),
('17:00:00', '03:30:00', '19:00:00', '1:00:00', 10.5, 1, 0, 1, 1, 1, 0, 0),
('06:45:00', '16:15:00', '08:45:00', '1:00:00', 9.5, 1, 0, 1, 1, 1, 0, 1),
('21:00:00', '04:15:00', '23:00:00', '0:30:00', 7.25, 0, 1, 0, 1, 0, 1, 0),
('11:15:00', '20:00:00', '13:15:00', '1:00:00', 8.75, 1, 1, 0, 0, 0, 1, 1),
('22:00:00', '08:30:00', '00:00:00', '1:00:00', 10.5, 1, 1, 1, 0, 1, 0, 1),
('21:15:00', '01:15:00', '23:30:00', '0:30:00', 4, 1, 1, 1, 0, 0, 0, 0),
('02:00:00', '09:45:00', '04:00:00', '0:30:00', 7.75, 0, 1, 1, 1, 1, 0, 0),
('08:30:00', '18:30:00', '10:45:00', '1:00:00', 10, 0, 0, 1, 1, 1, 1, 1),
('22:45:00', '05:30:00', '00:15:00', '0:30:00', 6.75, 1, 1, 1, 1, 0, 0, 1),
('23:30:00', '03:45:00', '01:45:00', '0:30:00', 4.25, 1, 0, 1, 0, 0, 0, 0),
('15:15:00', '02:30:00', '17:15:00', '1:00:00', 11.25, 0, 0, 0, 0, 1, 0, 0),
('20:45:00', '05:00:00', '22:00:00', '1:00:00', 8.25, 1, 0, 0, 0, 1, 0, 1),
('19:00:00', '04:30:00', '21:45:00', '1:00:00', 9.5, 1, 1, 1, 1, 1, 1, 1),
('10:30:00', '16:45:00', '12:45:00', '0:30:00', 6.25, 1, 1, 1, 1, 1, 0, 0),
('20:45:00', '03:30:00', '22:00:00', '0:30:00', 6.75, 1, 0, 0, 0, 0, 0, 1),
('01:45:00', '10:45:00', '03:45:00', '1:00:00', 9, 1, 1, 1, 1, 1, 1, 0),
('01:30:00', '13:30:00', '03:45:00', '1:00:00', 12, 0, 0, 0, 1, 1, 0, 1),
('19:45:00', '01:15:00', '21:30:00', '0:30:00', 5.5, 0, 0, 1, 0, 1, 0, 1),
('13:45:00', '01:15:00', '15:00:00', '1:00:00', 11.5, 0, 0, 1, 0, 1, 1, 1),
('19:45:00', '06:30:00', '21:00:00', '1:00:00', 10.75, 1, 0, 0, 1, 0, 1, 1),
('14:15:00', '19:00:00', '16:00:00', '0:30:00', 4.75, 1, 1, 0, 1, 1, 0, 0),
('10:30:00', '22:15:00', '12:15:00', '1:00:00', 11.75, 1, 0, 1, 0, 1, 1, 0),
('21:45:00', '05:30:00', '23:00:00', '0:30:00', 7.75, 1, 0, 1, 1, 0, 0, 0),
('20:45:00', '01:00:00', '22:15:00', '0:30:00', 4.25, 1, 1, 1, 0, 0, 1, 1),
('14:00:00', '22:00:00', '16:30:00', '0:30:00', 8, 0, 0, 1, 0, 0, 0, 0),
('17:30:00', '21:45:00', '19:30:00', '0:30:00', 4.25, 0, 1, 0, 1, 0, 0, 0),
('20:30:00', '08:00:00', '22:45:00', '1:00:00', 11.5, 0, 0, 1, 0, 0, 1, 1),
('15:00:00', '01:30:00', '17:00:00', '1:00:00', 10.5, 1, 0, 0, 0, 0, 1, 0),
('19:45:00', '02:15:00', '21:30:00', '0:30:00', 6.5, 0, 0, 0, 1, 1, 0, 1),
('03:00:00', '13:15:00', '05:30:00', '1:00:00', 10.25, 1, 0, 1, 0, 1, 0, 1),
('03:15:00', '13:45:00', '05:15:00', '1:00:00', 10.5, 0, 0, 1, 0, 1, 0, 1),
('03:00:00', '08:45:00', '05:30:00', '0:30:00', 5.75, 0, 0, 1, 0, 0, 1, 0),
('08:15:00', '16:15:00', '10:45:00', '0:30:00', 8, 0, 0, 1, 0, 0, 0, 1),
('04:45:00', '13:15:00', '06:00:00', '1:00:00', 8.5, 1, 1, 1, 1, 0, 0, 1),
('13:15:00', '22:00:00', '15:15:00', '1:00:00', 8.75, 1, 1, 1, 1, 1, 1, 1),
('11:15:00', '18:30:00', '13:00:00', '0:30:00', 7.25, 0, 1, 1, 0, 1, 0, 0),
('21:00:00', '04:15:00', '23:00:00', '0:30:00', 7.25, 1, 1, 0, 0, 1, 0, 0),
('00:00:00', '10:45:00', '02:15:00', '1:00:00', 10.75, 0, 0, 1, 1, 1, 1, 1),
('09:15:00', '20:00:00', '11:00:00', '1:00:00', 10.75, 1, 0, 1, 1, 0, 0, 1),
('12:30:00', '17:15:00', '14:30:00', '0:30:00', 4.75, 0, 0, 1, 0, 0, 0, 0),
('05:15:00', '11:45:00', '07:45:00', '0:30:00', 6.5, 0, 1, 0, 1, 1, 1, 1),
('10:00:00', '15:45:00', '12:00:00', '0:30:00', 5.75, 1, 1, 0, 1, 1, 1, 1),
('08:45:00', '20:30:00', '10:45:00', '1:00:00', 11.75, 0, 1, 0, 0, 1, 0, 1),
('01:45:00', '05:15:00', '03:15:00', '0:30:00', 3.5, 1, 0, 1, 0, 1, 1, 0),
('10:15:00', '15:00:00', '12:15:00', '0:30:00', 4.75, 0, 1, 0, 1, 1, 1, 0),
('21:30:00', '09:00:00', '23:45:00', '1:00:00', 11.5, 1, 0, 1, 0, 0, 0, 1),
('13:45:00', '21:00:00', '15:45:00', '0:30:00', 7.25, 1, 0, 1, 0, 1, 1, 1),
('18:00:00', '23:30:00', '20:00:00', '0:30:00', 5.5, 1, 1, 0, 0, 1, 0, 1),
('22:15:00', '03:45:00', '00:15:00', '0:30:00', 5.5, 1, 0, 1, 1, 0, 0, 1),
( '11:30:00', '22:45:00', '13:30:00', '1:00:00', 11.25, 1, 1, 0, 1, 0, 0, 1);
    ''')
    conn.commit()
    conn.close()
