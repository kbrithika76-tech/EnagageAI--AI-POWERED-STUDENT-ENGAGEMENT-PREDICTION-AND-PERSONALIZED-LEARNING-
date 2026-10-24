"""
EngageAI Backend — routes/prediction.py
GET  /students/me/prediction
POST /students/me/prediction/refresh
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.models.activity import ActivityEvent, Prediction
from backend.models.content import ContentProgress
from backend.models.quiz import QuizAttempt
from backend.auth.dependencies import get_current_user, require_student
from backend.services.ml_service import ml_service

router = APIRouter(prefix="/students/me/prediction", tags=["Real Bi-LSTM Prediction"])


@router.get("")
def get_prediction(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    pred = db.query(Prediction).filter(Prediction.student_id == current_user.id).first()
    if not pred or not pred.is_sufficient:
        return {
            "is_sufficient": False,
            "message": "Not enough learning activity yet. Watch videos and complete quizzes to generate engagement predictions!"
        }

    return {
        "is_sufficient": True,
        "predicted_class": pred.predicted_class,
        "engagement_level": pred.engagement_level,
        "low_probability": pred.low_probability,
        "medium_probability": pred.medium_probability,
        "high_probability": pred.high_probability,
        "confidence": pred.confidence,
        "prediction_timestamp": pred.prediction_timestamp.isoformat() if pred.prediction_timestamp else None
    }


@router.post("/refresh")
def refresh_prediction(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    # Fetch events & data for the student
    events = db.query(ActivityEvent).filter(ActivityEvent.student_id == current_user.id).all()
    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.student_id == current_user.id).all()
    content_progress = db.query(ContentProgress).filter(ContentProgress.student_id == current_user.id).all()

    # Run ML prediction pipeline
    res = ml_service.predict(events, quiz_attempts, content_progress, current_user.profile)

    pred = db.query(Prediction).filter(Prediction.student_id == current_user.id).first()

    if not res["sufficient_data"]:
        if pred:
            pred.is_sufficient = 0
            db.commit()
        return {
            "is_sufficient": False,
            "message": res["message"]
        }

    # Update or create prediction record
    if not pred:
        pred = Prediction(student_id=current_user.id)
        db.add(pred)

    pred.predicted_class = res["predicted_class"]
    pred.engagement_level = res["engagement_level"]
    pred.low_probability = res["low_probability"]
    pred.medium_probability = res["medium_probability"]
    pred.high_probability = res["high_probability"]
    pred.confidence = res["confidence"]
    pred.total_activity_count = len(events)
    pred.prediction_timestamp = datetime.utcnow()
    pred.is_sufficient = 1

    db.commit()
    db.refresh(pred)

    return {
        "is_sufficient": True,
        "predicted_class": pred.predicted_class,
        "engagement_level": pred.engagement_level,
        "low_probability": pred.low_probability,
        "medium_probability": pred.medium_probability,
        "high_probability": pred.high_probability,
        "confidence": pred.confidence,
        "prediction_timestamp": pred.prediction_timestamp.isoformat()
    }
