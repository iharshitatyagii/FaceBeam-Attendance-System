import sqlite3
import os

DB_NAME = 'facebeam.db'


if os.path.exists(DB_NAME):
    os.remove(DB_NAME)
    print(f"Removed old database '{DB_NAME}'.")

# SQL script to create all tables and insert all data
sql_script = """
-- Create Subjects Table
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Create Students Table
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    image_path TEXT NOT NULL,
    student_id TEXT UNIQUE,
    section TEXT,
    year TEXT
);

-- Create Timetable Table
CREATE TABLE timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects (id)
);

-- Create Attendance Table
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    subject_id INTEGER,
    student_db_id INTEGER,
    FOREIGN KEY (subject_id) REFERENCES subjects (id),
    FOREIGN KEY (student_db_id) REFERENCES students (id)
);

-- Insert all subjects from the timetable
INSERT INTO subjects (id, name) VALUES
(1, 'DataBase Management System'),
(2, 'Design and Analysis of Algorithm'),
(3, 'Web Technology'),
(4, 'Application of Soft Computing'),
(5, 'Object Oriented System Design'),
(6, 'Constitution of India, Law and Engg.');

-- Insert the weekly class schedule
-- Day of week: 0=Monday, 1=Tuesday, ..., 6=Sunday
INSERT INTO timetable (subject_id, day_of_week, start_time, end_time) VALUES
(1, 0, '08:50', '09:40'), -- Mon, DBMS
(5, 0, '09:40', '10:30'), -- Mon, OOSD
(3, 0, '10:30', '11:20'), -- Mon, WT
(4, 0, '11:20', '12:10'), -- Mon, ASC
(2, 0, '12:10', '13:00'), -- Mon, DAA
(1, 0, '14:40', '16:20'), -- Mon, DBMS Lab
(3, 1, '08:50', '09:40'), -- Tue, WT
(1, 1, '09:40', '10:30'), -- Tue, DBMS
(3, 1, '10:30', '11:20'), -- Tue, WT
(5, 1, '11:20', '12:10'), -- Tue, OOSD
(4, 1, '12:10', '13:00'), -- Tue, ASC
(4, 2, '08:50', '09:40'), -- Wed, ASC
(5, 2, '09:40', '10:30'), -- Wed, OOSD
(2, 2, '10:30', '11:20'), -- Wed, DAA
(6, 2, '11:20', '12:10'), -- Wed, COI
(3, 2, '12:10', '13:00'), -- Wed, WT
(2, 2, '14:40', '16:20'), -- Wed, DAA LAB
(2, 3, '08:50', '09:40'), -- Thu, DAA
(1, 3, '09:40', '10:30'), -- Thu, DBMS
(4, 3, '11:20', '12:10'), -- Thu, ASC
(3, 3, '13:50', '15:30'), -- Thu, WT LAB
(1, 4, '09:40', '10:30'), -- Fri, DBMS
(2, 4, '10:30', '11:20'), -- Fri, DAA
(6, 4, '11:20', '12:10'), -- Fri, COI
(1, 5, '12:40', '13:40'); -- Sat, DBMS
-- Insert a sample student record
INSERT INTO students (name, image_path, student_id, section, year) VALUES
('virat', 'virat.jpg', '2301430130091', 'IT-2', '3rd Year');
-- Insert a sample attendance record for the student
INSERT INTO attendance (name, timestamp, subject_id, student_db_id) VALUES
('virat', '2025-10-18 12:00:00', 6, 1); -- Attended 'COI' class

"""

try:
    # Connect to the database and execute the script
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    print(f"✅ Database '{DB_NAME}' has been created and populated successfully.")
except sqlite3.Error as e:
    print(f"An error occurred: {e}")