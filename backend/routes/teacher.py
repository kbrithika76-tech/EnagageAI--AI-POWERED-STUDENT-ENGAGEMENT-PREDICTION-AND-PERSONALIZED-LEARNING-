"""
EngageAI Backend — routes/teacher.py
GET  /teacher/students
GET  /teacher/students/{id}
GET  /teacher/at-risk
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from backend.database import get_db
from backend.models.user import User
from backend.models.activity import ActivityEvent, Prediction
from backend.models.content import ContentProgress
from backend.models.quiz import QuizAttempt
from backend.auth.dependencies import require_teacher
from backend.services.xai_service import get_student_explanation

router = APIRouter(prefix="/teacher", tags=["Teacher Dashboard & Monitoring"])


@router.get("/students")
def get_all_students(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    students = db.query(User).filter(User.role == "student").all()
    
    predictions_map = {p.student_id: p for p in db.query(Prediction).all()}

    res = []
    for s in students:
        pred = predictions_map.get(s.id)
        res.append({
            "student_id": s.id,
            "name": s.name,
            "email": s.email,
            "profile": s.profile,
            "prediction": {
                "engagement_level": pred.engagement_level if (pred and pred.is_sufficient) else "Insufficient Activity",
                "confidence": pred.confidence if (pred and pred.is_sufficient) else None,
                "low_prob": pred.low_probability if (pred and pred.is_sufficient) else None,
                "med_prob": pred.medium_probability if (pred and pred.is_sufficient) else None,
                "high_prob": pred.high_probability if (pred and pred.is_sufficient) else None,
            }
        })
    return res


@router.get("/at-risk")
def get_at_risk_students(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    # Fetch students with Low engagement or high low_probability
    preds = db.query(Prediction).filter(
        Prediction.is_sufficient == 1,
        (Prediction.engagement_level == "Low") | (Prediction.low_probability >= 0.4)
    ).all()

    at_risk = []
    for p in preds:
        student = db.query(User).filter(User.id == p.student_id).first()
        if student:
            # Determine risk reasons based on prediction and activity
            reasons = []
            if p.engagement_level == "Low":
                reasons.append("Bi-LSTM model predicted Low Engagement overall.")
            if p.low_probability >= 0.5:
                reasons.append(f"High Low-Engagement probability ({round(p.low_probability * 100, 1)}%).")

            at_risk.append({
                "student_id": student.id,
                "name": student.name,
                "email": student.email,
                "engagement_level": p.engagement_level,
                "risk_score": round(p.low_probability * 100.0, 1),
                "risk_reasons": reasons,
                "last_active": p.prediction_timestamp.isoformat() if p.prediction_timestamp else None
            })

    return at_risk


@router.get("/students/{student_id}")
def get_student_details_for_teacher(
    student_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    events = db.query(ActivityEvent).filter(ActivityEvent.student_id == student_id).all()
    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.student_id == student_id).all()
    content_progress = db.query(ContentProgress).filter(ContentProgress.student_id == student_id).all()
    pred = db.query(Prediction).filter(Prediction.student_id == student_id).first()

    explanation = get_student_explanation(db, student_id, events, quiz_attempts, content_progress, student.profile)

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "profile": student.profile
        },
        "prediction": {
            "engagement_level": pred.engagement_level if (pred and pred.is_sufficient) else "Insufficient Activity",
            "confidence": pred.confidence if (pred and pred.is_sufficient) else None,
            "low_prob": pred.low_probability if (pred and pred.is_sufficient) else None,
            "med_prob": pred.medium_probability if (pred and pred.is_sufficient) else None,
            "high_prob": pred.high_probability if (pred and pred.is_sufficient) else None,
        },
        "stats": {
            "total_events": len(events),
            "completed_videos": sum(1 for p in content_progress if p.is_completed),
            "completed_quizzes": len(quiz_attempts),
            "avg_quiz_score": round(sum(a.score_pct for a in quiz_attempts)/len(quiz_attempts), 1) if quiz_attempts else 0.0
        },
        "explanation": explanation
    }


@router.get("/ai-insights")
def get_teacher_ai_insights(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Class-level AI insights for teachers:
    engagement distribution, activity alerts, quiz performance summary.
    """
    students = db.query(User).filter(User.role == "student").all()
    preds = {p.student_id: p for p in db.query(Prediction).filter(Prediction.is_sufficient == 1).all()}
    all_events = db.query(ActivityEvent).all()
    all_attempts = db.query(QuizAttempt).all()

    # Engagement distribution
    dist = {"High": 0, "Medium": 0, "Low": 0, "Insufficient Activity": 0}
    for s in students:
        p = preds.get(s.id)
        level = p.engagement_level if p else "Insufficient Activity"
        dist[level] = dist.get(level, 0) + 1

    # Students with no events in last 7 days
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_this_week = {e.student_id for e in all_events if e.timestamp >= week_ago}
    inactive_count = sum(1 for s in students if s.id not in active_this_week)

    # Students with no quiz attempt
    students_with_quizzes = {a.student_id for a in all_attempts}
    no_quiz_count = sum(1 for s in students if s.id not in students_with_quizzes)

    # Average quiz score
    avg_score = round(sum(a.score_pct for a in all_attempts) / len(all_attempts), 1) if all_attempts else 0.0

    # Insight messages
    insights = []
    if dist["High"] > 0:
        insights.append({
            "type": "positive",
            "icon": "🚀",
            "message": f"{dist['High']} student(s) are showing High Engagement — keep up the momentum!",
            "action": "Consider assigning advanced resources to maintain their engagement."
        })
    if dist["Low"] > 0:
        insights.append({
            "type": "warning",
            "icon": "⚠️",
            "message": f"{dist['Low']} student(s) have Low Engagement predicted by the Bi-LSTM model.",
            "action": "Send targeted revision materials or schedule a check-in session."
        })
    if inactive_count > 0:
        insights.append({
            "type": "alert",
            "icon": "📉",
            "message": f"{inactive_count} student(s) had no activity in the past 7 days.",
            "action": "Send a re-engagement notification or short activity challenge."
        })
    if no_quiz_count > 0:
        insights.append({
            "type": "info",
            "icon": "📋",
            "message": f"{no_quiz_count} student(s) have not attempted any quiz yet.",
            "action": "Encourage quiz participation with a beginner-level assessment."
        })
    if avg_score < 60 and len(all_attempts) > 0:
        insights.append({
            "type": "warning",
            "icon": "📚",
            "message": f"Class average quiz score is {avg_score}% — below the 60% threshold.",
            "action": "Consider providing additional revision videos on weak topics."
        })

    return {
        "total_students": len(students),
        "engagement_distribution": dist,
        "inactive_this_week": inactive_count,
        "students_with_no_quiz": no_quiz_count,
        "avg_class_quiz_score": avg_score,
        "insights": insights
    }
