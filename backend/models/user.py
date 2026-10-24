"""
EngageAI Backend — models/user.py
SQLAlchemy ORM model for the users table.
"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from backend.database.db import Base


class User(Base):
    __tablename__ = "users"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(120), nullable=False)
    email        = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)   # null for OAuth-only users
    role         = Column(String(20), nullable=False, default="student")  # student | teacher | admin
    is_active    = Column(Boolean, default=True)
    profile_json = Column(Text, nullable=True)   # JSON blob for onboarding demographics
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    activity_events = relationship("ActivityEvent", back_populates="student", foreign_keys="ActivityEvent.student_id")
    quiz_attempts   = relationship("QuizAttempt", back_populates="student")
    content_progress = relationship("ContentProgress", back_populates="student")
    predictions     = relationship("Prediction", back_populates="student")

    @property
    def profile(self) -> dict:
        if self.profile_json:
            return json.loads(self.profile_json)
        return {}

    @profile.setter
    def profile(self, value: dict):
        self.profile_json = json.dumps(value)
