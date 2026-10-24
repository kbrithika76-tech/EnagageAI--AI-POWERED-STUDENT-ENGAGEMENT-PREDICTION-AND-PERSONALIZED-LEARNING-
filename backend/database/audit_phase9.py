import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import func

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database.db import SessionLocal
from backend.models.course import Course, CourseModule, Concept
from backend.models.content import LearningContent
from backend.models.quiz import Quiz, QuizQuestion
from backend.models.user import User

def run_audit():
    db: Session = SessionLocal()
    report = ["="*50, "PHASE 9 COURSE CONTENT AUDIT", "="*50, ""]
    
    try:
        courses = db.query(Course).all()
        modules = db.query(CourseModule).all()
        concepts = db.query(Concept).all()
        videos = db.query(LearningContent).filter(LearningContent.concept_id.isnot(None)).all()
        quizzes = db.query(Quiz).all()
        questions = db.query(QuizQuestion).all()
        users = db.query(User).count()
        
        report.append(f"Total Courses: {len(courses)}")
        report.append(f"Total Modules: {len(modules)}")
        report.append(f"Total Concepts: {len(concepts)}")
        report.append(f"Total Videos: {len(videos)}")
        report.append(f"Total Quizzes: {len(quizzes)}")
        report.append(f"Total Questions: {len(questions)}")
        report.append(f"Active Users (Preserved): {users}")
        report.append("-" * 50)

        # 1. Every course has modules
        courses_without_modules = [c for c in courses if not c.modules]
        report.append(f"1. Courses without modules: {len(courses_without_modules)}")
        
        # 2. Every module has concepts
        modules_without_concepts = [m for m in modules if not m.concepts]
        report.append(f"2. Modules without concepts: {len(modules_without_concepts)}")
        
        # 3. Every concept has a video
        concept_ids = {c.id for c in concepts}
        video_concept_ids = {v.concept_id for v in videos}
        concepts_without_videos = concept_ids - video_concept_ids
        report.append(f"3. Concepts without videos: {len(concepts_without_videos)}")
        
        # 4 & 5. Video Source Info & License Status
        missing_source_or_license = [v for v in videos if not v.source_name or not v.license_type]
        report.append(f"4 & 5. Videos missing source or license: {len(missing_source_or_license)}")
        
        # 6 & 7. Quizzes & Question counts per concept
        invalid_concept_quizzes = 0
        invalid_concept_qs = 0
        
        for c in concepts:
            v = next((vid for vid in videos if vid.concept_id == c.id), None)
            if not v:
                continue
                
            concept_quizzes = [q for q in quizzes if q.video_id == v.id]
            if len(concept_quizzes) != 3:
                invalid_concept_quizzes += 1
                
            easy_qs = db.query(QuizQuestion).join(Quiz).filter(Quiz.video_id == v.id, QuizQuestion.difficulty == 'easy').count()
            mod_qs = db.query(QuizQuestion).join(Quiz).filter(Quiz.video_id == v.id, QuizQuestion.difficulty == 'moderate').count()
            diff_qs = db.query(QuizQuestion).join(Quiz).filter(Quiz.video_id == v.id, QuizQuestion.difficulty == 'difficult').count()
            
            if easy_qs != 15 or mod_qs != 10 or diff_qs != 5:
                invalid_concept_qs += 1
                
        report.append(f"6. Concepts with incorrect quiz counts (not exactly 3): {invalid_concept_quizzes}")
        report.append(f"7. Concepts with incorrect question counts (not 15/10/5): {invalid_concept_qs}")
        
        # 8, 9, 10. Question fields validation
        missing_options = [q for q in questions if not q.option_a or not q.option_b or not q.option_c or not q.option_d]
        invalid_correct = [q for q in questions if q.correct_option not in ['a', 'b', 'c', 'd']]
        missing_expl = [q for q in questions if not q.explanation]
        
        report.append(f"8. Questions missing A/B/C/D: {len(missing_options)}")
        report.append(f"9. Questions with invalid correct_option: {len(invalid_correct)}")
        report.append(f"10. Questions missing explanation: {len(missing_expl)}")
        
        # 11 & 12. Duplicates
        q_texts = [q.question for q in questions]
        unique_texts = set(q_texts)
        duplicate_count = len(q_texts) - len(unique_texts)
        report.append(f"11 & 12. Total duplicate questions: {duplicate_count}")
        
        # Determine overall PASS / FAIL
        all_checks = (
            len(courses_without_modules) == 0 and
            len(modules_without_concepts) == 0 and
            len(concepts_without_videos) == 0 and
            len(missing_source_or_license) == 0 and
            invalid_concept_quizzes == 0 and
            invalid_concept_qs == 0 and
            len(missing_options) == 0 and
            len(invalid_correct) == 0 and
            len(missing_expl) == 0 and
            duplicate_count == 0
        )
        
        report.append("-" * 50)
        report.append("DATABASE AUDIT STATUS: " + ("PASS" if all_checks else "FAIL"))
        report.append("="*50)
        
        report_text = "\n".join(report)
        print(report_text)
        
        os.makedirs(os.path.join(BASE_DIR, "outputs", "reports"), exist_ok=True)
        with open(os.path.join(BASE_DIR, "outputs", "reports", "course_content_audit.txt"), "w") as f:
            f.write(report_text)
            
    finally:
        db.close()

if __name__ == "__main__":
    run_audit()
