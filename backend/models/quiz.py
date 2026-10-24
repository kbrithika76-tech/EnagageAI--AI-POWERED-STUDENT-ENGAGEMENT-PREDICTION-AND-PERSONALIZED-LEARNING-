"""
EngageAI Backend — models/quiz.py
SQLAlchemy ORM models for quizzes, questions, and attempts.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database.db import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    module      = Column(String(100), nullable=False, default="General")
    topic       = Column(String(100), nullable=True)
    difficulty  = Column(String(20), nullable=False, default="beginner")
    video_id    = Column(Integer, ForeignKey("learning_contents.id"), nullable=True)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    # Relationships
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts  = relationship("QuizAttempt", back_populates="quiz")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id             = Column(Integer, primary_key=True, index=True)
    quiz_id        = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question       = Column(Text, nullable=False)
    option_a       = Column(String(500), nullable=False)
    option_b       = Column(String(500), nullable=False)
    option_c       = Column(String(500), nullable=True)
    option_d       = Column(String(500), nullable=True)
    correct_option = Column(String(1), nullable=False)   # 'a' | 'b' | 'c' | 'd'
    explanation    = Column(Text, nullable=True)
    difficulty     = Column(String(50), nullable=True)
    marks          = Column(Integer, default=1)
    order_index    = Column(Integer, default=0)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id              = Column(Integer, primary_key=True, index=True)
    quiz_id         = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    student_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    score           = Column(Float, default=0.0)
    total_marks     = Column(Integer, default=0)
    score_pct       = Column(Float, default=0.0)   # 0.0–100.0
    completion_time = Column(Integer, nullable=True)   # seconds taken
    answers_json    = Column(Text, nullable=True)      # JSON: {question_id: chosen_option}
    attempt_number  = Column(Integer, default=1)
    started_at      = Column(DateTime, nullable=True)
    completed_at    = Column(DateTime, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    # Relationships
    quiz    = relationship("Quiz", back_populates="attempts")
    student = relationship("User", back_populates="quiz_attempts")
