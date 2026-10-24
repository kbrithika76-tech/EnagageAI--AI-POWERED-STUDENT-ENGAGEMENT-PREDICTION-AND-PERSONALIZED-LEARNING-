"""
EngageAI Backend — models/content.py
SQLAlchemy ORM models for learning content and student progress.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database.db import Base


class LearningContent(Base):
    __tablename__ = "learning_contents"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(255), nullable=False)
    description  = Column(Text, nullable=True)
    module       = Column(String(100), nullable=False, default="General")
    topic        = Column(String(100), nullable=True)
    content_type = Column(String(20), nullable=False, default="video")  # video | reading | resource
    video_url    = Column(String(500), nullable=True)   # YouTube embed URL or direct MP4 URL
    thumbnail_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)   # total duration in seconds
    difficulty   = Column(String(20), nullable=False, default="beginner")  # beginner | intermediate | advanced
    tags         = Column(String(500), nullable=True)   # comma-separated tags
    
    # Phase 8 additions
    source_name = Column(String(255), nullable=True)
    license_type = Column(String(255), nullable=True)
    attribution = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=True)
    allow_embedding = Column(Boolean, default=True)
    license_verified = Column(Integer, nullable=False, default=0)  # 0 = not verified, 1 = verified

    created_by   = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    # Phase 9 additions
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=True)

    # Relationships
    progress_records = relationship("ContentProgress", back_populates="content")
    concept = relationship("Concept", back_populates="videos")


class ContentProgress(Base):
    __tablename__ = "content_progress"

    id              = Column(Integer, primary_key=True, index=True)
    student_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id      = Column(Integer, ForeignKey("learning_contents.id"), nullable=False)
    watch_seconds   = Column(Integer, default=0)        # total seconds watched
    completion_pct  = Column(Float, default=0.0)        # 0.0–1.0
    is_completed    = Column(Boolean, default=False)
    last_watched_at = Column(DateTime, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("User", back_populates="content_progress")
    content = relationship("LearningContent", back_populates="progress_records")
