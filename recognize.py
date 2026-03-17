import face_recognition
import cv2
import os
import numpy as np
from PIL import Image, UnidentifiedImageError
from datetime import datetime
import sqlite3

DB_NAME = 'facebeam.db'
KNOWN_FACES_DIR = "known_faces"

def get_current_subject():
    
    now = datetime.now()
    current_day = now.weekday()
    current_time = now.strftime('%H:%M')
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        query = "SELECT subject_id FROM timetable WHERE day_of_week = ? AND start_time <= ? AND end_time >= ?"
        cursor.execute(query, (current_day, current_time, current_time))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Database error checking schedule: {e}")
    return None

print("Loading known faces...")
known_face_encodings = []
known_face_names = []
logged_names_today = {}

for filename in os.listdir(KNOWN_FACES_DIR):
    try:
        image_path = os.path.join(KNOWN_FACES_DIR, filename)
        pil_image = Image.open(image_path).convert("RGB")
        image = np.array(pil_image)
        encoding = face_recognition.face_encodings(image)[0]
        name = os.path.splitext(filename)[0].replace('_', ' ').title()
        known_face_encodings.append(encoding)
        known_face_names.append(name)
    except (IndexError, UnidentifiedImageError):
        print(f"⚠️ Warning: Could not process {filename}. Skipping.")

print("✅ Known faces loaded.")
video_capture = cv2.VideoCapture(0)

while True:
    current_subject_id = get_current_subject()
    ret, frame = video_capture.read()
    if not ret: break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

                if current_subject_id is not None:
                    if logged_names_today.get(current_subject_id) is None:
                        logged_names_today[current_subject_id] = []

                    if name not in logged_names_today[current_subject_id]:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        try:
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            
                            
                            # 1. Find the student's primary ID from the 'students' table.
                            cursor.execute("SELECT id FROM students WHERE name = ?", (name,))
                            student_id_result = cursor.fetchone()
                            
                            if student_id_result:
                                student_db_id = student_id_result[0]
                                
                                # 2. Insert the attendance record with the correct student_db_id.
                                cursor.execute(
                                    "INSERT INTO attendance (name, timestamp, subject_id, student_db_id) VALUES (?, ?, ?, ?)",
                                    (name, timestamp, current_subject_id, student_db_id)
                                )
                                conn.commit()
                                
                                logged_names_today[current_subject_id].append(name)
                                print(f"✅ Logged '{name}' for Subject ID {current_subject_id}")
                            else:
                                print(f"⚠️ Could not find student '{name}' in the students table.")

                            conn.close()
                        except sqlite3.Error as e:
                            print(f"Database error: {e}")

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    display_text = "No Scheduled Class"
    if current_subject_id:
        display_text = f"Class In Session (Subject ID: {current_subject_id})"
    
    cv2.putText(frame, display_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.imshow('FaceBeam', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
print("👋 Program terminated.")