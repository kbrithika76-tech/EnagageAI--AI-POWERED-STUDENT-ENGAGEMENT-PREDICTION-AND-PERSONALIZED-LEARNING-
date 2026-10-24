import os
import sys
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database.db import SessionLocal
from backend.models.user import User
from backend.models.content import LearningContent
from backend.models.quiz import Quiz, QuizQuestion

def seed_phase8():
    db = SessionLocal()
    data_path = os.path.join(os.path.dirname(__file__), 'seed_data.json')
    
    with open(data_path, 'r') as f:
        videos_data = json.load(f)

    print(f"Loaded {len(videos_data)} videos from JSON.")

    admin = db.query(User).filter(User.role == "admin").first()
    admin_id = admin.id if admin else None

    videos_added = 0
    quizzes_added = 0
    questions_added = 0

    for v_data in videos_data:
        # Check if video already exists to avoid duplicates
        existing = db.query(LearningContent).filter(LearningContent.title == v_data["title"]).first()
        if existing:
            print(f"Skipping existing video: {v_data['title']}")
            continue

        vid = LearningContent(
            title=v_data["title"],
            description=v_data["description"],
            module=v_data["module"],
            topic=v_data["topic"],
            content_type="video",
            video_url=v_data["video_url"],
            thumbnail_url=v_data["thumbnail_url"],
            duration_seconds=v_data["duration_seconds"],
            difficulty=v_data["difficulty"],
            tags=v_data["tags"],
            source_name=v_data["source_name"],
            license_type=v_data["license_type"],
            attribution=v_data["attribution"],
            source_url=v_data["source_url"],
            allow_embedding=v_data["allow_embedding"],
            created_by=admin_id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(vid)
        db.flush() # to get vid.id
        videos_added += 1

        for q_data in v_data["quizzes"]:
            quiz = Quiz(
                title=q_data["title"],
                description=q_data["description"],
                module=q_data["module"],
                topic=q_data["topic"],
                difficulty=q_data["difficulty"],
                video_id=vid.id,
                created_by=admin_id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(quiz)
            db.flush()
            quizzes_added += 1

            for i, qq_data in enumerate(q_data["questions"]):
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question=qq_data["question"],
                    option_a=qq_data["option_a"],
                    option_b=qq_data["option_b"],
                    option_c=qq_data["option_c"],
                    option_d=qq_data["option_d"],
                    correct_option=qq_data["correct_option"],
                    explanation=qq_data["explanation"],
                    difficulty=qq_data["difficulty"],
                    marks=qq_data["marks"],
                    order_index=i
                )
                db.add(question)
                questions_added += 1
                
    db.commit()
    db.close()
    
    print("--------------------------------------------------")
    print("Phase 8 Seeding Summary:")
    print(f"New Videos added: {videos_added}")
    print(f"New Quizzes added: {quizzes_added}")
    print(f"New Questions added: {questions_added}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    seed_phase8()
