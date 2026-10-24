from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.database.db import get_db
from backend.models.course import Course, CourseModule, Concept
from backend.models.content import LearningContent

router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("/", response_model=List[Dict[str, Any]])
def get_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).order_by(Course.order_index).all()
    result = []
    for c in courses:
        result.append({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "difficulty": c.difficulty,
            "duration_estimate": c.duration_estimate,
            "module_count": len(c.modules),
            "progress_pct": 0  # To be calculated based on user progress later
        })
    return result

@router.get("/{course_id}", response_model=Dict[str, Any])
def get_course_details(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    modules_data = []
    for m in course.modules:
        concepts_data = []
        for c in m.concepts:
            # check if concept has video
            video = db.query(LearningContent).filter(LearningContent.concept_id == c.id).first()
            concepts_data.append({
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "order_index": c.order_index,
                "has_video": video is not None,
                "video_id": video.id if video else None,
                "is_completed": False # To be added dynamically based on user
            })
        modules_data.append({
            "id": m.id,
            "title": m.title,
            "description": m.description,
            "learning_objectives": m.learning_objectives,
            "order_index": m.order_index,
            "concepts": concepts_data
        })
        
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "difficulty": course.difficulty,
        "duration_estimate": course.duration_estimate,
        "modules": modules_data
    }
