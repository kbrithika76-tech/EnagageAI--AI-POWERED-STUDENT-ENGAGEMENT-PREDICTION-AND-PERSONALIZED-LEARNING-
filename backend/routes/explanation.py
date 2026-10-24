"""
EngageAI Backend — routes/explanation.py
GET /students/me/explanation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.models.activity import ActivityEvent
from backend.models.content import ContentProgress
from backend.models.quiz import QuizAttempt
from backend.auth.dependencies import get_current_user, require_student
from backend.services.xai_service import get_student_explanation

router = APIRouter(prefix="/students/me/explanation", tags=["Explainable AI (XAI)"])


@router.get("")
def get_explanation(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    events = db.query(ActivityEvent).filter(ActivityEvent.student_id == current_user.id).all()
    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.student_id == current_user.id).all()
    content_progress = db.query(ContentProgress).filter(ContentProgress.student_id == current_user.id).all()

    explanation_data = get_student_explanation(
        db, current_user.id, events, quiz_attempts, content_progress, current_user.profile
    )

    return {
        "student_id": current_user.id,
        "attention": explanation_data["attention"],
        "shap": explanation_data["shap"]
    }
