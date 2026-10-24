"""
EngageAI Backend — models/course.py
SQLAlchemy ORM models for courses, modules, and concepts.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database.db import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(50), nullable=False, default="beginner")
    duration_estimate = Column(String(100), nullable=True)  # e.g., "4 Weeks", "12 Hours"
    is_active = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    modules = relationship("CourseModule", back_populates="course", cascade="all, delete-orphan", order_by="CourseModule.order_index")


class CourseModule(Base):
    __tablename__ = "course_modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    learning_objectives = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)

    # Relationships
    course = relationship("Course", back_populates="modules")
    concepts = relationship("Concept", back_populates="module", cascade="all, delete-orphan", order_by="Concept.order_index")


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("course_modules.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)

    # Relationships
    module = relationship("CourseModule", back_populates="concepts")
    videos = relationship("LearningContent", back_populates="concept")
