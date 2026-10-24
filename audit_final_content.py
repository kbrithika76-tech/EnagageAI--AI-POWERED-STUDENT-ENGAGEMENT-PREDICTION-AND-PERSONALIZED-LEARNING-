import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'backend', 'engageai.db')
REPORT_PATH = os.path.join(BASE_DIR, 'outputs', 'reports', 'final_content_audit.txt')

def run_audit():
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    audit_results = []
    status = True

    # 1. SQLite Integrity
    cursor.execute("PRAGMA integrity_check")
    integrity = cursor.fetchone()[0]
    audit_results.append(f"SQLite Integrity: {integrity}")
    if integrity != "ok":
        status = False

    # 2. Total counts
    cursor.execute("SELECT COUNT(*) FROM courses")
    c_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM course_modules")
    m_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM concepts")
    con_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM learning_contents")
    vid_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM quizzes")
    q_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM quiz_questions")
    qq_count = cursor.fetchone()[0]

    audit_results.append(f"\n--- TOTAL COUNTS ---")
    audit_results.append(f"Courses: {c_count}")
    audit_results.append(f"Modules: {m_count}")
    audit_results.append(f"Concepts: {con_count}")
    audit_results.append(f"Videos: {vid_count}")
    audit_results.append(f"Quizzes: {q_count}")
    audit_results.append(f"Questions: {qq_count}")

    # 3. Hierarchy Integrity
    # Check if any concept lacks a module
    cursor.execute("SELECT COUNT(*) FROM concepts WHERE module_id IS NULL OR module_id NOT IN (SELECT id FROM course_modules)")
    orphan_concepts = cursor.fetchone()[0]
    audit_results.append(f"\nHierarchy Integrity - Orphan Concepts: {orphan_concepts}")
    if orphan_concepts > 0: status = False

    # 4. Video Coverage and Duplicates
    cursor.execute("""
        SELECT c.id, c.title, l.id as vid_id, l.video_url, l.license_type, l.license_verified
        FROM concepts c
        LEFT JOIN learning_contents l ON c.id = l.concept_id
    """)
    concept_videos = cursor.fetchall()

    missing_videos = []
    urls = set()
    duplicates = []
    license_issues = []

    for cv in concept_videos:
        if not cv['vid_id']:
            missing_videos.append(cv['title'])
        else:
            url = cv['video_url']
            if url in urls:
                duplicates.append(url)
            urls.add(url)
            
            if not cv['license_type']:
                license_issues.append(cv['title'])

    audit_results.append(f"\n--- VIDEO CHECKS ---")
    audit_results.append(f"Concepts Missing Videos: {len(missing_videos)}")
    if missing_videos:
        status = False
        for m in missing_videos:
            audit_results.append(f"  - {m}")
            
    audit_results.append(f"Duplicate Video URLs: {len(duplicates)}")
    if duplicates:
        for d in set(duplicates):
            audit_results.append(f"  - {d}")

    audit_results.append(f"Videos with Missing License Info: {len(license_issues)}")
    if license_issues:
        status = False

    # 5. Quiz Integrity (15/10/5 per concept)
    # Get all concepts
    cursor.execute("SELECT id, title FROM concepts")
    concepts = cursor.fetchall()
    
    quiz_issues = []
    
    for concept in concepts:
        cid = concept['id']
        cursor.execute("SELECT difficulty, id FROM quizzes WHERE concept_id = ?", (cid,))
        quizzes = cursor.fetchall()
        
        q_map = {q['difficulty']: q['id'] for q in quizzes}
        
        if 'easy' not in q_map or 'moderate' not in q_map or 'difficult' not in q_map:
            quiz_issues.append(f"Concept '{concept['title']}' missing one or more required quizzes (Easy/Moderate/Difficult).")
            continue
            
        # Check questions count
        for diff, expected in [('easy', 15), ('moderate', 10), ('difficult', 5)]:
            cursor.execute("SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = ?", (q_map[diff],))
            count = cursor.fetchone()[0]
            if count != expected:
                quiz_issues.append(f"Concept '{concept['title']}' - {diff} quiz has {count} questions (expected {expected}).")

    audit_results.append(f"\n--- QUIZ INTEGRITY ---")
    audit_results.append(f"Quiz Integrity Issues: {len(quiz_issues)}")
    if quiz_issues:
        status = False
        for qi in quiz_issues[:20]: # show first 20
            audit_results.append(f"  - {qi}")
        if len(quiz_issues) > 20:
            audit_results.append(f"  ... and {len(quiz_issues)-20} more issues.")

    # Final Status
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("FINAL CONTENT AUDIT REPORT\n")
        f.write("="*50 + "\n")
        for res in audit_results:
            f.write(res + "\n")
            
        f.write("\n" + "="*50 + "\n")
        if status:
            f.write("CONTENT STATUS: PASS\n")
        else:
            f.write("CONTENT STATUS: FAIL\n")

    conn.close()
    print(f"Final audit complete. Report generated at {REPORT_PATH}")

if __name__ == "__main__":
    run_audit()
