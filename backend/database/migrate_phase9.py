import os
import sys
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database.db import engine, Base
from backend.models.course import Course, CourseModule, Concept
from backend.models.content import LearningContent

def migrate():
    print("="*60)
    print("PHASE 9 DATABASE MIGRATION")
    print("="*60)

    db_path = os.path.join(BASE_DIR, "backend", "engageai.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}!")
        return

    # 1. Add concept_id to learning_contents using raw SQL (safer for SQLite)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Check if column exists
        c.execute("PRAGMA table_info(learning_contents)")
        columns = [col[1] for col in c.fetchall()]
        if 'concept_id' not in columns:
            print("Adding 'concept_id' column to 'learning_contents'...")
            c.execute("ALTER TABLE learning_contents ADD COLUMN concept_id INTEGER REFERENCES concepts(id)")
            conn.commit()
            print("Column 'concept_id' added successfully.")
        else:
            print("Column 'concept_id' already exists in 'learning_contents'.")
    except Exception as e:
        print(f"Error altering learning_contents: {e}")
    finally:
        conn.close()

    # 2. Create new tables (courses, course_modules, concepts) using SQLAlchemy
    print("Creating new tables for courses, course_modules, concepts...")
    Base.metadata.create_all(bind=engine)
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
