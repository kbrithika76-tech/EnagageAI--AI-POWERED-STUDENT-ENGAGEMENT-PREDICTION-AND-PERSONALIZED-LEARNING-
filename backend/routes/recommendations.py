"""
EngageAI Backend — routes/recommendations.py
GET /students/me/recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.models.activity import Prediction
from backend.auth.dependencies import get_current_user, require_student
from backend.services.recommendation_service import get_recommendations, get_quiz_recommendations

router = APIRouter(prefix="/students/me/recommendations", tags=["Personalized Recommendations"])


@router.get("")
def get_student_recommendations(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    pred = db.query(Prediction).filter(Prediction.student_id == current_user.id).first()
    engagement_level = pred.engagement_level if (pred and pred.is_sufficient) else None

    content_recs = get_recommendations(db, current_user.id, engagement_level, limit=6)
    quiz_recs = get_quiz_recommendations(db, current_user.id, engagement_level, limit=3)

    return {
        "engagement_level": engagement_level or "Low (Default Onboarding)",
        "content_recommendations": content_recs,
        "quiz_recommendations": quiz_recs
    }
