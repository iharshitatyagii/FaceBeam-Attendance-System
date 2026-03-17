import sqlite3
import os
import shutil
import sys

DB_NAME = 'facebeam.db'
KNOWN_FACES_DIR = 'known_faces'

def register_new_student():
    """A command-line tool to register a new student."""
    print("--- FaceBeam: New Student Registration ---")
    
    try:
        # 1. Get student details from user input
        full_name = input("Enter student's full name: ").strip()
        roll_number = input("Enter Roll Number: ").strip()
        branch = input("Enter Branch : ").strip()
        section = input("Enter Section : ").strip()
        year = input("Enter Year : ").strip()
        college_id = input("Enter College ID : ").strip()
        photo_path_input = input(r"Enter the FULL path to the student's photo: ")
        
    
        # Strip whitespace AND any surrounding quotes
        photo_path = photo_path_input.strip().strip('"')

        # Basic validation
        if not all([full_name, roll_number, branch, section, year, college_id, photo_path]):
            print("\n❌ Error: All fields are required. Please try again.")
            return

        # 2. Process and copy the photo
        if not os.path.exists(photo_path):
            print(f"\n❌ Error: Photo not found at '{photo_path}'.")
            return
            
        # Create a standardized filename 
        image_filename = full_name.replace(' ', '_').lower() + os.path.splitext(photo_path)[1]
        destination_path = os.path.join(KNOWN_FACES_DIR, image_filename)
        
        shutil.copy(photo_path, destination_path)
        print(f"✅ Photo successfully copied to '{destination_path}'.")

        # 3. Add student details to the database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # NOTE: We use student_id = roll_number, but you can change this
        student_id_from_user = roll_number 
        
        cursor.execute(
            "INSERT INTO students (name, image_path, student_id, section, year, roll_number, branch, college_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (full_name, image_filename, student_id_from_user, section, year, roll_number, branch, college_id)
        )
        conn.commit()
        conn.close()
        
        print(f"\n✅ Student '{full_name}' successfully added to the database!")

    except sqlite3.IntegrityError:
        print(f"\n❌ Database Error: A student with that Name or Student ID may already exist.")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        # Clean up the copied file if database insert failed
        if 'destination_path' in locals() and os.path.exists(destination_path):
            os.remove(destination_path)
            print(f"Cleaned up file: {destination_path}")
    finally:
        print("--- Registration script finished. ---")


if __name__ == '__main__':
    register_new_student()