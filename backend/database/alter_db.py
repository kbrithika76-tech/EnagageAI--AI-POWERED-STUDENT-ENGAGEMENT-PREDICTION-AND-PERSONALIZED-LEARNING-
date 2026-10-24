import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "engageai.db")

def add_column_if_not_exists(cursor, table_name, column_definition):
    col_name = column_definition.split()[0]
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    if col_name not in columns:
        print(f"Adding column {col_name} to {table_name}")
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")
    else:
        print(f"Column {col_name} already exists in {table_name}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # learning_contents additions
    add_column_if_not_exists(cursor, "learning_contents", "source_name VARCHAR(255)")
    add_column_if_not_exists(cursor, "learning_contents", "license_type VARCHAR(255)")
    add_column_if_not_exists(cursor, "learning_contents", "attribution TEXT")
    add_column_if_not_exists(cursor, "learning_contents", "source_url VARCHAR(500)")
    add_column_if_not_exists(cursor, "learning_contents", "allow_embedding BOOLEAN DEFAULT 1")

    # quizzes additions
    add_column_if_not_exists(cursor, "quizzes", "video_id INTEGER")

    # quiz_questions additions
    add_column_if_not_exists(cursor, "quiz_questions", "explanation TEXT")
    add_column_if_not_exists(cursor, "quiz_questions", "difficulty VARCHAR(50)")

    # quiz_attempts additions
    add_column_if_not_exists(cursor, "quiz_attempts", "attempt_number INTEGER DEFAULT 1")

    conn.commit()
    conn.close()
    print("Database alterations completed safely.")

if __name__ == "__main__":
    main()
