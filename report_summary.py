import os, sqlite3, json
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'backend', 'engageai.db')
REPORT_PATH = os.path.join(PROJECT_ROOT, 'outputs', 'reports', 'final_summary_report.txt')
os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Basic counts
c.execute('SELECT COUNT(*) AS cnt FROM concepts')
concepts_cnt = c.fetchone()['cnt']

c.execute('SELECT COUNT(*) AS cnt FROM learning_contents')
learning_cnt = c.fetchone()['cnt']

c.execute('SELECT COUNT(*) AS cnt FROM quizzes')
quizzes_cnt = c.fetchone()['cnt']

c.execute('SELECT COUNT(*) AS cnt FROM quiz_questions')
questions_cnt = c.fetchone()['cnt']

# Quiz difficulty distribution (assuming a column 'difficulty' in quizzes)
# If not present, fallback to counting per quiz id prefix (just placeholder)
try:
    c.execute("SELECT difficulty, COUNT(*) AS cnt FROM quizzes GROUP BY difficulty")
    diff_counts = {row['difficulty']: row['cnt'] for row in c.fetchall()}
except Exception:
    diff_counts = {}

# Verify per-difficulty question counts per quiz (assuming relation quiz_id -> questions)
# For each quiz, count its questions.
quiz_question_counts = {}
c.execute('SELECT id FROM quizzes')
quiz_ids = [row['id'] for row in c.fetchall()]
for qid in quiz_ids:
    c.execute('SELECT COUNT(*) AS cnt FROM quiz_questions WHERE quiz_id = ?', (qid,))
    cnt = c.fetchone()['cnt']
    quiz_question_counts[qid] = cnt

# Prepare report
with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write('FINAL SUMMARY REPORT\n')
    f.write('='*50 + '\n\n')
    f.write(f'Total concepts: {concepts_cnt}\n')
    f.write(f'Total learning_contents (videos) rows: {learning_cnt}\n')
    f.write(f'Total quizzes: {quizzes_cnt}\n')
    f.write(f'Total quiz_questions: {questions_cnt}\n')
    f.write('\nQuiz difficulty distribution (if available):\n')
    for diff, cnt in diff_counts.items():
        f.write(f' - {diff}: {cnt}\n')
    f.write('\nQuestion count per quiz (sample first 10):\n')
    for i, (qid, cnt) in enumerate(quiz_question_counts.items()):
        if i >= 10:
            break
        f.write(f' - Quiz ID {qid}: {cnt} questions\n')
    f.write('\n')
    f.write('Video population summary (from previous report) would be referenced in video_population_report.txt.\n')
    f.write('Audit warnings (from audit_videos.py) may be found in audit log.\n')

print('Summary report written to', REPORT_PATH)
