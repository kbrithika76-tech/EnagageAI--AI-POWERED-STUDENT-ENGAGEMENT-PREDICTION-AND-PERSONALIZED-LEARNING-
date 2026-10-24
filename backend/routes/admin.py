"""
EngageAI Backend — routes/admin.py
GET  /admin/users
GET  /admin/analytics
PATCH /admin/users/{id}/role
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.models.user import User
from backend.models.activity import ActivityEvent, Prediction
from backend.models.content import LearningContent
from backend.models.quiz import Quiz
from backend.auth.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["Admin System Management"])


class RoleUpdateRequest(BaseModel):
    role: str


@router.get("/users")
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat()
        }
        for u in users
    ]


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    body: RoleUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if body.role not in ("student", "teacher", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role specified.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.role = body.role
    db.commit()
    return {"message": "Role updated successfully", "user_id": user_id, "new_role": user.role}


@router.get("/analytics")
def get_system_analytics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    total_students = db.query(User).filter(User.role == "student").count()
    total_teachers = db.query(User).filter(User.role == "teacher").count()
    total_videos = db.query(LearningContent).filter(LearningContent.content_type == "video").count()
    total_quizzes = db.query(Quiz).count()
    total_events = db.query(ActivityEvent).count()

    preds = db.query(Prediction).filter(Prediction.is_sufficient == 1).all()
    dist = {"Low": 0, "Medium": 0, "High": 0}
    for p in preds:
        if p.engagement_level in dist:
            dist[p.engagement_level] += 1

    return {
        "user_counts": {
            "total": total_users,
            "students": total_students,
            "teachers": total_teachers
        },
        "content_counts": {
            "videos": total_videos,
            "quizzes": total_quizzes,
            "activity_events": total_events
        },
        "engagement_distribution": dist,
        "model_performance_summary": {
            "test_accuracy": "99.37%",
            "macro_f1": "0.9937",
            "weighted_f1": "0.9937",
            "architecture": "Bi-LSTM + Temporal Attention + Static Feature Fusion"
        }
    }
