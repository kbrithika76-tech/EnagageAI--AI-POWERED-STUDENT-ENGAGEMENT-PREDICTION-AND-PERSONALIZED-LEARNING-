"""
EngageAI Backend — routes/students.py
GET /students/me
PUT /students/me/profile
GET /students/me/dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from backend.database import get_db
from backend.models.user import User
from backend.models.activity import ActivityEvent, Prediction
from backend.models.content import ContentProgress, LearningContent
from backend.models.quiz import QuizAttempt
from backend.auth.dependencies import get_current_user, require_student
from backend.services.ml_service import ml_service
from backend.services.recommendation_service import get_recommendations

router = APIRouter(prefix="/students", tags=["Student Profile & Dashboard"])


class ProfileUpdateRequest(BaseModel):
    gender: Optional[str] = Field(None, example="M")
    region: Optional[str] = Field(None, example="South East Region")
    highest_education: Optional[str] = Field(None, example="A Level or Equivalent")
    imd_band: Optional[str] = Field(None, example="50-60%")
    age_band: Optional[str] = Field(None, example="0-35")
    disability: Optional[str] = Field(None, example="N")
    studied_credits: Optional[float] = Field(None, example=60.0)
    num_of_prev_attempts: Optional[float] = Field(None, example=0.0)


@router.get("/me")
def get_student_profile(current_user: User = Depends(require_student)):
    return {
        "student_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "profile": current_user.profile,
        "created_at": current_user.created_at
    }


@router.put("/me/profile")
def update_student_profile(
    body: ProfileUpdateRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    profile = current_user.profile
    update_data = body.dict(exclude_unset=True)
    profile.update(update_data)
    current_user.profile = profile
    db.commit()
    db.refresh(current_user)
    return {
        "message": "Profile updated successfully",
        "profile": current_user.profile
    }


@router.get("/me/dashboard")
def get_student_dashboard(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    # 1. Fetch cached prediction or generate/retrieve
    prediction_record = db.query(Prediction).filter(Prediction.student_id == current_user.id).first()
    
    # Fetch student activity events
    events = db.query(ActivityEvent).filter(ActivityEvent.student_id == current_user.id).order_by(ActivityEvent.timestamp.desc()).all()
    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.student_id == current_user.id).all()
    content_progress = db.query(ContentProgress).filter(ContentProgress.student_id == current_user.id).all()

    # 2. Activity statistics
    total_events = len(events)
    total_watched_sec = sum(p.watch_seconds for p in content_progress)
    completed_videos = sum(1 for p in content_progress if p.is_completed)
    completed_quizzes = len(quiz_attempts)
    avg_quiz_score = float(sum(a.score_pct for a in quiz_attempts) / completed_quizzes) if completed_quizzes > 0 else 0.0

    # 3. Prediction Status
    if not prediction_record:
        # Run prediction if not cached
        pred_res = ml_service.predict(events, quiz_attempts, content_progress, current_user.profile)
        if pred_res.get("sufficient_data"):
            prediction_record = Prediction(
                student_id=current_user.id,
                predicted_class=pred_res["predicted_class"],
                engagement_level=pred_res["engagement_level"],
                low_probability=pred_res["low_probability"],
                medium_probability=pred_res["medium_probability"],
                high_probability=pred_res["high_probability"],
                confidence=pred_res["confidence"],
                total_activity_count=total_events,
                is_sufficient=1
            )
            db.add(prediction_record)
            db.commit()
            db.refresh(prediction_record)

    pred_data = None
    if prediction_record and prediction_record.is_sufficient:
        pred_data = {
            "predicted_class": prediction_record.predicted_class,
            "engagement_level": prediction_record.engagement_level,
            "low_probability": prediction_record.low_probability,
            "medium_probability": prediction_record.medium_probability,
            "high_probability": prediction_record.high_probability,
            "confidence": prediction_record.confidence,
            "is_sufficient": True
        }
    else:
        pred_data = {
            "is_sufficient": False,
            "message": "Not enough learning activity yet. Watch videos and complete quizzes to generate engagement predictions!"
        }

    # 4. Top recommendations
    eng_level = pred_data.get("engagement_level") if pred_data.get("is_sufficient") else None
    recommendations = get_recommendations(db, current_user.id, eng_level, limit=4)

    # 5. Recent activity feed (last 5)
    recent_activity = [
        {
            "id": e.id,
            "event_type": e.event_type,
            "timestamp": e.timestamp.isoformat(),
            "duration": e.duration
        }
        for e in events[:5]
    ]

    return {
        "student": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email
        },
        "stats": {
            "total_events": total_events,
            "watch_time_minutes": round(total_watched_sec / 60.0, 1),
            "completed_videos": completed_videos,
            "completed_quizzes": completed_quizzes,
            "avg_quiz_score": round(avg_quiz_score, 1)
        },
        "prediction": pred_data,
        "recommendations": recommendations,
        "recent_activity": recent_activity
    }


@router.get("/me/progress")
def get_student_progress(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Returns weekly activity breakdown, streak, and per-content progress
    for the student progress analytics page.
    """
    from datetime import datetime, timedelta
    from collections import defaultdict

    events = db.query(ActivityEvent).filter(
        ActivityEvent.student_id == current_user.id
    ).order_by(ActivityEvent.timestamp).all()

    content_progress = db.query(ContentProgress).filter(
        ContentProgress.student_id == current_user.id
    ).all()

    quiz_attempts = db.query(QuizAttempt).filter(
        QuizAttempt.student_id == current_user.id
    ).all()

    # ── Weekly event bucketing (last 8 weeks) ────────────────────────────────
    now = datetime.utcnow()
    weekly = []
    for i in range(7, -1, -1):
        week_start = now - timedelta(weeks=i+1)
        week_end   = now - timedelta(weeks=i)
        label = f"W-{i}" if i > 0 else "This Week"
        count = sum(1 for e in events if week_start <= e.timestamp < week_end)
        weekly.append({"week": label, "events": count})

    # ── Active days / streak ─────────────────────────────────────────────────
    active_dates = sorted({e.timestamp.date() for e in events})
    streak = 0
    if active_dates:
        today = datetime.utcnow().date()
        check = today
        for d in reversed(active_dates):
            if d == check or d == check - timedelta(days=1):
                streak += 1
                check = d
            else:
                break

    # ── Content progress summary ──────────────────────────────────────────────
    total_content = db.query(LearningContent).filter(LearningContent.is_active == True).count()
    completed_videos = sum(1 for p in content_progress if p.is_completed)
    total_watch_sec  = sum(p.watch_seconds for p in content_progress)

    # ── Quiz performance by topic ─────────────────────────────────────────────
    from backend.models.quiz import Quiz
    quiz_map = {q.id: q for q in db.query(Quiz).all()}
    topic_scores = defaultdict(list)
    for a in quiz_attempts:
        q = quiz_map.get(a.quiz_id)
        topic = q.topic or q.module if q else "General"
        topic_scores[topic].append(a.score_pct)

    topic_performance = [
        {
            "topic": topic,
            "avg_score": round(sum(scores) / len(scores), 1),
            "attempts": len(scores)
        }
        for topic, scores in topic_scores.items()
    ]

    return {
        "weekly_activity": weekly,
        "streak_days": streak,
        "total_active_days": len(active_dates),
        "total_events": len(events),
        "completed_videos": completed_videos,
        "total_content_available": total_content,
        "watch_time_minutes": round(total_watch_sec / 60.0, 1),
        "completed_quizzes": len(quiz_attempts),
        "avg_quiz_score": round(sum(a.score_pct for a in quiz_attempts) / len(quiz_attempts), 1) if quiz_attempts else 0.0,
        "topic_performance": topic_performance,
    }


@router.get("/me/achievements")
def get_student_achievements(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Computes gamification data (XP, badges, streaks) from existing
    activity events and quiz/content progress records.
    """
    from datetime import datetime, timedelta

    events = db.query(ActivityEvent).filter(ActivityEvent.student_id == current_user.id).all()
    content_progress = db.query(ContentProgress).filter(ContentProgress.student_id == current_user.id).all()
    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.student_id == current_user.id).all()
    prediction = db.query(Prediction).filter(
        Prediction.student_id == current_user.id, Prediction.is_sufficient == 1
    ).first()

    completed_videos = sum(1 for p in content_progress if p.is_completed)
    completed_quizzes = len(quiz_attempts)
    avg_score = sum(a.score_pct for a in quiz_attempts) / len(quiz_attempts) if quiz_attempts else 0

    # XP calculation
    xp = (len(events) * 5) + (completed_videos * 50) + (completed_quizzes * 30)
    level = max(1, xp // 200 + 1)
    xp_to_next = (level * 200) - xp

    # Streak
    active_dates = sorted({e.timestamp.date() for e in events})
    streak = 0
    if active_dates:
        check = datetime.utcnow().date()
        for d in reversed(active_dates):
            if d == check or d == check - __import__('datetime').timedelta(days=1):
                streak += 1
                check = d
            else:
                break

    # Badge logic
    badges = []
    if len(events) >= 1:
        badges.append({"id": "first_login", "name": "First Login", "icon": "🚀", "earned": True, "description": "Logged in and started your journey."})
    if completed_videos >= 1:
        badges.append({"id": "first_video", "name": "Video Learner", "icon": "🎬", "earned": True, "description": "Completed your first video lesson."})
    if completed_videos >= 5:
        badges.append({"id": "binge_watcher", "name": "Binge Watcher", "icon": "📺", "earned": True, "description": "Completed 5 video lessons."})
    if completed_quizzes >= 1:
        badges.append({"id": "quiz_starter", "name": "Quiz Starter", "icon": "📝", "earned": True, "description": "Attempted your first quiz."})
    if completed_quizzes >= 3:
        badges.append({"id": "quiz_master", "name": "Quiz Master", "icon": "🏆", "earned": True, "description": "Completed 3 or more quizzes."})
    if avg_score >= 80:
        badges.append({"id": "high_scorer", "name": "High Scorer", "icon": "⭐", "earned": True, "description": "Achieved 80%+ average quiz score."})
    if streak >= 3:
        badges.append({"id": "streak_3", "name": "3-Day Streak", "icon": "🔥", "earned": True, "description": "Active for 3 consecutive days."})
    if streak >= 7:
        badges.append({"id": "streak_7", "name": "7-Day Streak", "icon": "💫", "earned": True, "description": "Active for 7 consecutive days."})
    if prediction and prediction.engagement_level == "High":
        badges.append({"id": "high_engagement", "name": "Highly Engaged", "icon": "🧠", "earned": True, "description": "Bi-LSTM predicted High Engagement."})

    # Unearned badges (motivational)
    earned_ids = {b["id"] for b in badges}
    all_possible = [
        {"id": "first_login",     "name": "First Login",     "icon": "🚀", "description": "Log in and start your journey."},
        {"id": "first_video",     "name": "Video Learner",   "icon": "🎬", "description": "Complete your first video."},
        {"id": "binge_watcher",   "name": "Binge Watcher",   "icon": "📺", "description": "Complete 5 videos."},
        {"id": "quiz_starter",    "name": "Quiz Starter",    "icon": "📝", "description": "Attempt your first quiz."},
        {"id": "quiz_master",     "name": "Quiz Master",     "icon": "🏆", "description": "Complete 3 quizzes."},
        {"id": "high_scorer",     "name": "High Scorer",     "icon": "⭐", "description": "Get 80%+ average quiz score."},
        {"id": "streak_3",        "name": "3-Day Streak",    "icon": "🔥", "description": "Be active 3 days in a row."},
        {"id": "streak_7",        "name": "7-Day Streak",    "icon": "💫", "description": "Be active 7 days in a row."},
        {"id": "high_engagement", "name": "Highly Engaged",  "icon": "🧠", "description": "Reach High Engagement prediction."},
        {"id": "course_finisher", "name": "Course Finisher", "icon": "🎓", "description": "Complete all content in a module."},
        {"id": "consistent",      "name": "Consistent Learner","icon": "📅","description": "Active for 14 days total."},
    ]
    for b in all_possible:
        if b["id"] not in earned_ids:
            badges.append({**b, "earned": False})

    return {
        "xp": xp,
        "level": level,
        "xp_to_next_level": max(0, xp_to_next),
        "streak_days": streak,
        "badges": badges,
        "total_events": len(events),
        "completed_videos": completed_videos,
        "completed_quizzes": completed_quizzes,
    }


@router.get("/me/my-learning")
def get_my_learning(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Returns all content the student has interacted with, plus their progress.
    """
    progress_records = db.query(ContentProgress).filter(
        ContentProgress.student_id == current_user.id
    ).all()

    progress_map = {p.content_id: p for p in progress_records}
    content_ids = list(progress_map.keys())

    if not content_ids:
        # Return all beginner content as "suggested starts"
        content = db.query(LearningContent).filter(
            LearningContent.is_active == True,
            LearningContent.difficulty == "beginner"
        ).limit(6).all()
        return {
            "in_progress": [],
            "completed": [],
            "suggested": [
                {
                    "id": c.id,
                    "title": c.title,
                    "module": c.module,
                    "difficulty": c.difficulty,
                    "duration_seconds": c.duration_seconds,
                    "video_url": c.video_url,
                    "thumbnail_url": c.thumbnail_url
                }
                for c in content
            ]
        }

    all_content = db.query(LearningContent).filter(
        LearningContent.id.in_(content_ids)
    ).all()

    in_progress = []
    completed = []

    for c in all_content:
        prog = progress_map.get(c.id)
        duration = c.duration_seconds or 300
        watch_pct = min(100, round((prog.watch_seconds / duration) * 100)) if prog else 0

        item = {
            "id": c.id,
            "title": c.title,
            "module": c.module,
            "difficulty": c.difficulty,
            "duration_seconds": duration,
            "watch_seconds": prog.watch_seconds if prog else 0,
            "watch_pct": watch_pct,
            "is_completed": prog.is_completed if prog else False,
            "video_url": c.video_url,
            "thumbnail_url": c.thumbnail_url,
        }
        if prog and prog.is_completed:
            completed.append(item)
        else:
            in_progress.append(item)

    return {
        "in_progress": in_progress,
        "completed": completed,
        "suggested": []
    }


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

@router.post("/me/chat")
def chat_with_ai(
    body: ChatRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    import os
    import openai
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503, 
            detail="AI assistance is currently unavailable. Please try again later."
        )

    openai.api_key = api_key

    # Combine context into system prompt
    context_str = ""
    if body.context:
        ctx = body.context
        context_str = (
            f"\nStudent Context:\n"
            f"- Name: {ctx.get('name', 'Student')}\n"
            f"- Engagement Level: {ctx.get('level', 'Unknown')}\n"
            f"- Confidence: {ctx.get('confidence', 0)*100}%\n"
            f"- Videos Completed: {ctx.get('completed_videos', 0)}\n"
            f"- Quizzes Completed: {ctx.get('completed_quizzes', 0)}\n"
            f"- Avg Quiz Score: {ctx.get('avg_score', 0)}%\n"
            f"- Active Streak: {ctx.get('streak', 0)} days\n"
        )

    system_prompt = (
        "You are 'EngageAI Coach', a helpful, encouraging educational AI assistant for students. "
        "Keep your answers concise, engaging, and directly related to learning. "
        "Use the student's context to personalize advice if relevant."
        f"{context_str}"
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": body.message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        ai_message = response.choices[0].message.content
        return {"response": ai_message}
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI assistance is currently unavailable. Please try again later."
        )


