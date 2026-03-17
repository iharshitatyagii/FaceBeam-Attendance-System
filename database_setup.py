import sqlite3

DB_NAME = 'facebeam.db'
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# 1. Update Students Table with Admission Details
try:
    cursor.execute("ALTER TABLE students ADD COLUMN student_id TEXT UNIQUE")
    cursor.execute("ALTER TABLE students ADD COLUMN section TEXT")
    cursor.execute("ALTER TABLE students ADD COLUMN year TEXT")
    print("Columns added to 'students' table.")
except sqlite3.OperationalError:
    print("Columns for admission details already exist in 'students' table.")

# 2. Update Attendance Table to use student_id instead of name
# This is better for data integrity
try:
    cursor.execute("ALTER TABLE attendance ADD COLUMN student_db_id INTEGER REFERENCES students(id)")
    print("Column 'student_db_id' added to 'attendance' table.")
except sqlite3.OperationalError:
    print("Column 'student_db_id' already exists in 'attendance' table.")

conn.commit()
conn.close()

print(f"✅ Database '{DB_NAME}' schema updated successfully.")