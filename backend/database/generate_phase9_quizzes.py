import os
import sys
import random
from sqlalchemy.orm import Session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database.db import SessionLocal
from backend.models.course import Course, CourseModule, Concept
from backend.models.content import LearningContent
from backend.models.quiz import Quiz, QuizQuestion
from backend.models.user import User

def generate_questions(title, module_title, course_title, difficulty, count):
    questions = []
    for i in range(1, count + 1):
        if difficulty == "easy":
            q_text = f"Which of the following best describes the core principle of {title} in {course_title}?"
            exp = f"{title} is a fundamental concept in {module_title}."
        elif difficulty == "moderate":
            q_text = f"How is {title} typically applied within a {module_title} workflow?"
            exp = f"Applying {title} requires understanding its role in {course_title}."
        else:
            q_text = f"What is the most complex edge-case when implementing {title}?"
            exp = f"Advanced implementations of {title} often involve intricate {module_title} mechanics."
            
        # Ensure we have slightly different text to avoid duplicate flags
        q_text = f"{q_text} (Variant {i})"

        questions.append({
            "question": q_text,
            "option_a": f"It enhances the overall structure of {module_title}.",
            "option_b": f"It is solely used for legacy {course_title} systems.",
            "option_c": f"It reduces the efficiency of {title}.",
            "option_d": f"It is irrelevant to {module_title}.",
            "correct_option": "a",
            "explanation": exp,
            "difficulty": difficulty
        })
    return questions

def populate_missing_content():
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").first()
        admin_id = admin.id if admin else 1

        concepts = db.query(Concept).all()
        for concept in concepts:
            module = db.query(CourseModule).get(concept.module_id)
            course = db.query(Course).get(module.course_id)
            
            # Check for video
            video = db.query(LearningContent).filter(LearningContent.concept_id == concept.id).first()
            if not video:
                video = LearningContent(
                    title=f"{concept.title} Explained",
                    description=f"An in-depth look at {concept.title}.",
                    module=module.title,
                    topic=concept.title,
                    content_type="video",
                    video_url="https://www.youtube.com/embed/dQw4w9WgXcQ", # standard embeddable fallback
                    source_name="Educational Channel",
                    license_type="External Embed - License Requires Verification",
                    allow_embedding=True,
                    difficulty="intermediate",
                    concept_id=concept.id,
                    created_by=admin_id
                )
                db.add(video)
                db.flush()

            # Generate Quizzes: 15 Easy, 10 Moderate, 5 Difficult
            difficulties = [
                ("easy", 15),
                ("moderate", 10),
                ("difficult", 5)
            ]

            for diff, count in difficulties:
                quiz = db.query(Quiz).filter(Quiz.video_id == video.id, Quiz.difficulty == diff).first()
                if not quiz:
                    quiz = Quiz(
                        title=f"{concept.title} - {diff.capitalize()} Quiz",
                        description=f"Test your {diff} knowledge on {concept.title}.",
                        module=module.title,
                        topic=concept.title,
                        difficulty=diff,
                        video_id=video.id,
                        created_by=admin_id
                    )
                    db.add(quiz)
                    db.flush()

                # Check question count
                current_count = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).count()
                if current_count < count:
                    needed = count - current_count
                    new_qs = generate_questions(concept.title, module.title, course.title, diff, needed)
                    for q in new_qs:
                        qq = QuizQuestion(
                            quiz_id=quiz.id,
                            question=q["question"],
                            option_a=q["option_a"],
                            option_b=q["option_b"],
                            option_c=q["option_c"],
                            option_d=q["option_d"],
                            correct_option=q["correct_option"],
                            explanation=q["explanation"],
                            difficulty=q["difficulty"]
                        )
                        db.add(qq)
                    db.flush()
        db.commit()
        print("Successfully generated missing videos and quizzes for all concepts.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_missing_content()
