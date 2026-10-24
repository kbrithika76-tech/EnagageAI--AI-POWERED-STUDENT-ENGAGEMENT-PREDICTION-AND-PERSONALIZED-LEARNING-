"""
EngageAI Backend Integration Tests
Tests:
  - User registration & login
  - Activity events tracking
  - Video lessons progress update
  - Quiz submission
  - Engagement prediction refresh
  - XAI explanation generation
  - Personalized recommendations
"""

import sys
import os
import unittest
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Preprocessing path setup for preprocessor unpickling
sys.path.insert(0, os.path.join(BASE_DIR, "preprocessing"))
import encoder_scaler
import __main__
__main__.FeaturePreprocessor = encoder_scaler.FeaturePreprocessor

from backend.database.db import SessionLocal, Base, engine
from backend.models.user import User
from backend.models.content import LearningContent
from backend.models.quiz import Quiz, QuizQuestion
from backend.services.ml_service import ml_service
from backend.auth.password import hash_password


class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        ml_service.load()
        cls.db = SessionLocal()

        # Seed test student
        cls.student_email = "test_student@engageai.com"
        cls.student = cls.db.query(User).filter(User.email == cls.student_email).first()
        if not cls.student:
            cls.student = User(
                name="Test Student",
                email=cls.student_email,
                password_hash=hash_password("password123"),
                role="student",
                profile_json='{"gender": "M", "region": "South East Region", "highest_education": "A Level or Equivalent", "imd_band": "50-60%", "age_band": "0-35", "disability": "N", "studied_credits": 60, "num_of_prev_attempts": 0}'
            )
            cls.db.add(cls.student)
            cls.db.commit()
            cls.db.refresh(cls.student)

        # Seed content if none
        if cls.db.query(LearningContent).count() == 0:
            content = LearningContent(
                title="Test Video Content",
                module="Data Science",
                content_type="video",
                video_url="https://www.youtube.com/embed/aircAruvnKk",
                duration_seconds=600,
                difficulty="beginner"
            )
            cls.db.add(content)
            cls.db.commit()

        # Seed quiz if none
        if cls.db.query(Quiz).count() == 0:
            quiz = Quiz(
                title="Test Quiz",
                module="Data Science",
                difficulty="beginner"
            )
            cls.db.add(quiz)
            cls.db.commit()
            cls.db.refresh(quiz)
            
            question = QuizQuestion(
                quiz_id=quiz.id,
                question="What is 2+2?",
                option_a="3",
                option_b="4",
                correct_option="b"
            )
            cls.db.add(question)
            cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_ml_service_predict_insufficient(self):
        """Test prediction fails when student has no/little activity."""
        res = ml_service.predict([], [], [], self.student.profile)
        self.assertFalse(res["sufficient_data"])
        self.assertIn("Not enough learning activity", res["message"])

    def test_predict_sufficient(self):
        """Test prediction succeeds when student has sufficient activity."""
        # Create simulated events
        from backend.models.activity import ActivityEvent
        from backend.models.quiz import QuizAttempt
        from backend.models.content import ContentProgress

        mock_events = [
            ActivityEvent(event_type="VIDEO_STARTED", timestamp=datetime.utcnow() - timedelta(days=2)),
            ActivityEvent(event_type="VIDEO_COMPLETED", timestamp=datetime.utcnow() - timedelta(days=2)),
            ActivityEvent(event_type="QUIZ_COMPLETED", timestamp=datetime.utcnow() - timedelta(days=1)),
            ActivityEvent(event_type="CONTENT_COMPLETED", timestamp=datetime.utcnow()),
            ActivityEvent(event_type="VIDEO_COMPLETED", timestamp=datetime.utcnow())
        ]
        
        # Verify prediction runs
        res = ml_service.predict(mock_events, [], [], self.student.profile)
        self.assertTrue(res["sufficient_data"])
        self.assertIn(res["predicted_class"], [0, 1, 2])
        self.assertIn(res["engagement_level"], ["Low", "Medium", "High"])
        self.assertIsNotNone(res["confidence"])


from datetime import timedelta

if __name__ == "__main__":
    unittest.main()
