from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
import sqlite3
import os
import base64
from collections import defaultdict
from datetime import datetime

app = Flask(__name__, template_folder='webapp/templates')
DB_NAME = 'facebeam.db'
KNOWN_FACES_DIR = 'known_faces'

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to fetch the list of all registered students
@app.route('/api/students')
def api_students():
    student_names = []
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM students ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        student_names = [row[0] for row in rows]
    except sqlite3.Error as e:
        print(f"Database error fetching student list: {e}")
    return jsonify(student_names)

# Route to serve a specific student's photo
@app.route('/student_photo/<filename>')
def student_photo(filename):
    return send_from_directory(KNOWN_FACES_DIR, filename)

# Route for the individual student dashboard (handles GET and POST)
@app.route('/student/<student_name>', methods=['GET', 'POST'])
def student_dashboard(student_name):
    image_filename = student_name.replace(' ', '_').lower() + '.jpg'
    
    admission_details = {}
    status = None
    selected_subject = None
    selected_date = None
    attendance_percentage = 0.0
    
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch all subjects for the dropdown
        cursor.execute("SELECT id, name FROM subjects ORDER BY name")
        subjects = cursor.fetchall()

        # Handle form submission for checking status
        if request.method == 'POST':
            selected_subject = request.form['subject_id']
            selected_date = request.form['date']
            
            query = "SELECT COUNT(*) FROM attendance WHERE name = ? AND subject_id = ? AND date(timestamp) = ?"
            cursor.execute(query, (student_name, selected_subject, selected_date))
            record_count = cursor.fetchone()[0]
            status = 'Present' if record_count > 0 else 'Absent'

        # Fetch admission details
        cursor.execute("SELECT student_id, section, year, roll_number, branch, college_id FROM students WHERE name = ?", (student_name,))
        student_data = cursor.fetchone()
        if student_data:
            admission_details = {
                'Roll Number': student_data['roll_number'],
                'Branch': student_data['branch'],
                'Section': student_data['section'],
                'Year': student_data['year'],
                'College ID': student_data['college_id']
            }
        
        # CALCULATE OVERALL ATTENDANCE PERCENTAGE
        
        cursor.execute("SELECT COUNT(DISTINCT date(timestamp)) FROM attendance")
        total_days_with_records = cursor.fetchone()[0] or 1
        
        cursor.execute("SELECT COUNT(*) FROM timetable")
        total_scheduled_classes_per_week = cursor.fetchone()[0]
        
        total_classes_held = (total_days_with_records / 5) * total_scheduled_classes_per_week
        if total_classes_held == 0: total_classes_held = 1

        cursor.execute("SELECT COUNT(*) FROM attendance WHERE name = ?", (student_name,))
        total_attended = cursor.fetchone()[0]

        if total_classes_held > 0:
            attendance_percentage = round((total_attended / total_classes_held) * 100, 2)
            
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error on student dashboard: {e}")
        subjects = []

    return render_template('student_dashboard.html', 
                           student_name=student_name, 
                           image_filename=image_filename,
                           details=admission_details,
                           subjects=subjects,
                           status=status,
                           selected_subject=selected_subject,
                           selected_date=selected_date,
                           attendance_percentage=attendance_percentage)

# --- Student Registration Routes ---
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form['name']
    student_id = request.form.get('student_id')
    section = request.form.get('section')
    year = request.form.get('year')
    roll_number = request.form.get('roll_number')
    branch = request.form.get('branch')
    college_id = request.form.get('college_id')
    image_data = request.form['image_data']

    if not all([name, image_data]):
        return "Error: Name and image data are required.", 400

    filename = name.replace(' ', '_').lower() + '.jpg'
    filepath = os.path.join(KNOWN_FACES_DIR, filename)

    try:
        header, encoded = image_data.split(',', 1)
        image_bytes = base64.b64decode(encoded)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (name, image_path, student_id, section, year, roll_number, branch, college_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, filename, student_id, section, year, roll_number, branch, college_id)
        )
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error during registration: {e}")
        return "An error occurred during registration.", 500

    return redirect(url_for('student_dashboard', student_name=name))


@app.route('/delete_student/<student_name>', methods=['POST'])
def delete_student(student_name):
    conn = None # Initialize conn to None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row # Use row factory for easier access
        cursor = conn.cursor()

        # 1. Find the student in the database first
        cursor.execute("SELECT id, image_path FROM students WHERE name = ?", (student_name,))
        student_data = cursor.fetchone()

        if not student_data:
            print(f"Student '{student_name}' not found in database.")
            return jsonify({'success': False, 'message': f'Student {student_name} not found.'}), 404

        student_db_id = student_data['id']
        image_filename = student_data['image_path']

        # 2. Delete the student's image file using the path from the database
        filepath = os.path.join(KNOWN_FACES_DIR, image_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted image file: {filepath}")
        else:
            print(f"Warning: Image file not found at {filepath} (might have been deleted previously).")

        # 3. Delete records from the database using the student's ID
        # Delete from attendance table first due to potential foreign key links
        cursor.execute("DELETE FROM attendance WHERE student_db_id = ? OR name = ?", (student_db_id, student_name)) # Added name fallback just in case
        # Delete from students table
        cursor.execute("DELETE FROM students WHERE id = ?", (student_db_id,))
        
        conn.commit()
        print(f"Successfully deleted records for student: {student_name} (ID: {student_db_id})")

        conn.close()
        conn = None # Reset conn after closing

        return jsonify({'success': True, 'message': f'Student {student_name} deleted successfully.'})

    except Exception as e:
        print(f"Error deleting student '{student_name}': {e}") # Log the specific error
        # Ensure connection is closed on error
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'An error occurred while deleting {student_name}. Check server logs.'}), 500


# --- Admin Dashboard Routes ---
@app.route('/admin')
def admin_dashboard():
    return render_template('admin.html')

@app.route('/api/live_class')
def api_live_class():
    now = datetime.now()
    day_of_week = now.weekday()
    current_time = now.strftime('%H:%M')
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT s.name as subject_name, t.start_time, t.end_time
        FROM timetable t JOIN subjects s ON t.subject_id = s.id
        WHERE t.day_of_week = ? AND t.start_time <= ? AND t.end_time >= ?
    """
    cursor.execute(query, (day_of_week, current_time, current_time))
    current_class = cursor.fetchone()
    conn.close()
    
    return jsonify(dict(current_class) if current_class else {})

@app.route('/api/absentees')
def api_absentees():
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    live_class_data = api_live_class().get_json()
    if not live_class_data:
        conn.close()
        return jsonify([])

    cursor.execute("SELECT id FROM subjects WHERE name = ?", (live_class_data['subject_name'],))
    subject_id_res = cursor.fetchone()
    if not subject_id_res:
        conn.close()
        return jsonify([])
    subject_id = subject_id_res['id']

    cursor.execute("SELECT name FROM students")
    all_students = {row['name'] for row in cursor.fetchall()}

    query = "SELECT name FROM attendance WHERE subject_id = ? AND date(timestamp) = ?"
    cursor.execute(query, (subject_id, today_str))
    present_students = {row['name'] for row in cursor.fetchall()}

    absent_students = sorted(list(all_students - present_students))
    conn.close()
    
    return jsonify([{'name': name} for name in absent_students])




if __name__ == '__main__':
    app.run(debug=True)

