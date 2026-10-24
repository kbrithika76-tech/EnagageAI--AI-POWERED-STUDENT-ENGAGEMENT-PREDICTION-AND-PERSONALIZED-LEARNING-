import os
import shutil
from datetime import datetime

def backup_database():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'backend', 'engageai.db')
    BACKUP_DIR = os.path.join(BASE_DIR, 'backend', 'backups')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"engageai_backup_{timestamp}.sqlite")
    
    shutil.copy2(DB_PATH, backup_path)
    print(f"Successfully created backup at: {backup_path}")

if __name__ == '__main__':
    backup_database()
