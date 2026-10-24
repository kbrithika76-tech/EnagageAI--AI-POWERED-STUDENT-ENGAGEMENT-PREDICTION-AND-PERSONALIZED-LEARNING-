"""
EngageAI Backend — database/seed.py

Seeds the SQLite database with:
  1. Demo users (student, teacher, admin)
  2. Free sample YouTube educational videos (MIT OpenCourseWare, Khan Academy)
  3. Sample quizzes & questions
"""

import sys
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database.db import Base, engine, SessionLocal
from backend.models.user import User
from backend.models.content import LearningContent
from backend.models.quiz import Quiz, QuizQuestion
from backend.auth.password import hash_password


def seed_database():
    print("[Seed] Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # 1. Seed Users
    if db.query(User).count() == 0:
        print("[Seed] Seeding users...")
        users = [
            User(
                name="Student User",
                email="student@engageai.com",
                password_hash=hash_password("password123"),
                role="student",
                profile_json='{"gender": "M", "region": "South East Region", "highest_education": "A Level or Equivalent", "imd_band": "50-60%", "age_band": "0-35", "disability": "N", "studied_credits": 60, "num_of_prev_attempts": 0}'
            ),
            User(
                name="Teacher User",
                email="teacher@engageai.com",
                password_hash=hash_password("password123"),
                role="teacher"
            ),
            User(
                name="Admin User",
                email="admin@engageai.com",
                password_hash=hash_password("password123"),
                role="admin"
            )
        ]
        db.add_all(users)
        db.commit()

    # 2. Seed Videos
    if db.query(LearningContent).count() == 0:
        print("[Seed] Seeding videos...")
        videos = [
            LearningContent(
                title="Introduction to Machine Learning & AI Principles",
                description="Comprehensive introduction to core supervised learning algorithms, features, and model training concepts.",
                module="Data Science",
                topic="Machine Learning Basics",
                content_type="video",
                video_url="https://www.youtube.com/embed/aircAruvnKk",
                thumbnail_url="https://img.youtube.com/vi/aircAruvnKk/hqdefault.jpg",
                duration_seconds=600,
                difficulty="beginner",
                tags="ML, AI, Python, Basics"
            ),
            LearningContent(
                title="Deep Learning & Neural Networks Fundamentals",
                description="Learn the fundamentals of feedforward networks, backpropagation, and activation functions.",
                module="Deep Learning",
                topic="Neural Networks",
                content_type="video",
                video_url="https://www.youtube.com/embed/IHZwWFHWa-w",
                thumbnail_url="https://img.youtube.com/vi/IHZwWFHWa-w/hqdefault.jpg",
                duration_seconds=900,
                difficulty="intermediate",
                tags="Deep Learning, Neural Networks, PyTorch"
            ),
            LearningContent(
                title="Recurrent Neural Networks (RNNs) & LSTM Networks",
                description="Understand sequence processing, vanishing gradients, and how Long Short-Term Memory (LSTM) cells operate.",
                module="Deep Learning",
                topic="Sequential Modeling",
                content_type="video",
                video_url="https://www.youtube.com/embed/LHXXI4-0EkE",
                thumbnail_url="https://img.youtube.com/vi/LHXXI4-0EkE/hqdefault.jpg",
                duration_seconds=1200,
                difficulty="intermediate",
                tags="RNN, LSTM, Sequences, Time Series"
            ),
            LearningContent(
                title="Attention Mechanisms & Transformers Explained",
                description="Explore how temporal attention mechanisms compute soft alignment weights to focus on key sequence steps.",
                module="Deep Learning",
                topic="Attention Models",
                content_type="video",
                video_url="https://www.youtube.com/embed/dS3m_V3Z6nU",
                thumbnail_url="https://img.youtube.com/vi/dS3m_V3Z6nU/hqdefault.jpg",
                duration_seconds=1500,
                difficulty="advanced",
                tags="Attention, Transformers, XAI, Deep Learning"
            )
        ]
        db.add_all(videos)
        db.commit()

    # 3. Seed Quizzes
    if db.query(Quiz).count() == 0:
        print("[Seed] Seeding quizzes...")
        q1 = Quiz(
            title="Machine Learning Foundations Quiz",
            description="Test your knowledge of basic machine learning concepts.",
            module="Data Science",
            topic="Machine Learning Basics",
            difficulty="beginner"
        )
        db.add(q1)
        db.flush()

        questions = [
            QuizQuestion(
                quiz_id=q1.id,
                question="What is the main goal of supervised learning?",
                option_a="Grouping unlabeled data into clusters",
                option_b="Learning a mapping function from input features to known target labels",
                option_c="Maximizing reward through trial and error",
                option_d="Reducing dimensionality automatically",
                correct_option="b",
                marks=1,
                order_index=0
            ),
            QuizQuestion(
                quiz_id=q1.id,
                question="Which algorithm is best suited for binary classification?",
                option_a="Linear Regression",
                option_b="K-Means Clustering",
                option_c="Logistic Regression",
                option_d="Principal Component Analysis",
                correct_option="c",
                marks=1,
                order_index=1
            )
        ]
        db.add_all(questions)
        db.commit()

    db.close()
    print("[Seed] Database seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
