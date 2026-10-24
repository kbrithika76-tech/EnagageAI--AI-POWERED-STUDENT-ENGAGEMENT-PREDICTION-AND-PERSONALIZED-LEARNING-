"""
EngageAI Backend — services/recommendation_service.py

Rule-based + engagement-level recommendation engine.
Recommendations depend on:
  - Engagement level (Low/Medium/High)
  - Quiz performance
  - Content completion
  - Weak topics (based on quiz scores per topic)
"""

from typing import List
from sqlalchemy.orm import Session
from backend.models.content import LearningContent, ContentProgress
from backend.models.quiz import Quiz, QuizAttempt


def get_recommendations(
    db: Session,
    student_id: int,
    engagement_level: str | None,
    limit: int = 6,
) -> List[dict]:
    """
    Returns a list of recommended content items with reasons.
    """
    # Fetch student's existing progress
    completed_ids = {
        p.content_id for p in
        db.query(ContentProgress).filter(
            ContentProgress.student_id == student_id,
            ContentProgress.is_completed == True
        ).all()
    }

    # Fetch all active content
    all_content = db.query(LearningContent).filter(LearningContent.is_active == True).all()

    # Fetch quiz attempts
    attempts = db.query(QuizAttempt).filter(QuizAttempt.student_id == student_id).all()
    avg_quiz_score = (
        sum(a.score_pct for a in attempts) / len(attempts) if attempts else 0.0
    )

    # ── DIFFICULTY TARGETING ──────────────────────────────────────────────────
    if engagement_level == "Low" or engagement_level is None:
        target_difficulty = ["beginner"]
        reason_prefix = "Recommended to build foundational understanding"
    elif engagement_level == "Medium":
        target_difficulty = ["beginner", "intermediate"]
        reason_prefix = "Recommended to deepen your understanding"
    else:  # High
        target_difficulty = ["intermediate", "advanced"]
        reason_prefix = "Recommended to challenge and extend your knowledge"

    # ── SCORE-BASED ADJUSTMENTS ───────────────────────────────────────────────
    if avg_quiz_score < 50 and engagement_level != "Low":
        target_difficulty = ["beginner", "intermediate"]
        reason_prefix = "Recommended to improve your assessment performance"
    elif avg_quiz_score >= 80:
        target_difficulty = ["intermediate", "advanced"]

    recommendations = []

    # 1. Incomplete content first (most relevant)
    for content in all_content:
        if content.id in completed_ids:
            continue
        if content.difficulty not in target_difficulty:
            continue
        recommendations.append({
            "content_id"     : content.id,
            "title"          : content.title,
            "content_type"   : content.content_type,
            "topic"          : content.topic or content.module,
            "difficulty"     : content.difficulty,
            "reason"         : f"{reason_prefix}: {content.title}.",
            "relevance_score": _score_content(content, engagement_level, avg_quiz_score),
            "video_url"      : content.video_url,
            "thumbnail_url"  : content.thumbnail_url,
            "duration_seconds": content.duration_seconds,
        })

    # 2. Completed content for review if High engagement and good scores
    if engagement_level == "High" and len(recommendations) < limit:
        for content in all_content:
            if content.id not in completed_ids:
                continue
            if content.difficulty in ["advanced"]:
                recommendations.append({
                    "content_id"    : content.id,
                    "title"         : content.title,
                    "content_type"  : content.content_type,
                    "topic"         : content.topic or content.module,
                    "difficulty"    : content.difficulty,
                    "reason"        : f"Review this advanced topic to solidify mastery: {content.title}.",
                    "relevance_score": 0.5,
                    "video_url"     : content.video_url,
                    "thumbnail_url" : content.thumbnail_url,
                    "duration_seconds": content.duration_seconds,
                })

    # Sort by relevance score descending
    recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
    return recommendations[:limit]


def _score_content(content: LearningContent, engagement_level: str | None, avg_quiz_score: float) -> float:
    """Simple relevance scoring for content items."""
    score = 1.0

    # Bonus for matching engagement target difficulty
    level_difficulty = {
        "Low"   : {"beginner": 1.0, "intermediate": 0.3, "advanced": 0.0},
        "Medium": {"beginner": 0.6, "intermediate": 1.0, "advanced": 0.4},
        "High"  : {"beginner": 0.2, "intermediate": 0.8, "advanced": 1.0},
    }
    if engagement_level in level_difficulty:
        score *= level_difficulty[engagement_level].get(content.difficulty, 0.5)

    # Bonus for video content (more engaging for low/medium)
    if content.content_type == "video" and engagement_level in ("Low", "Medium"):
        score *= 1.2

    return min(1.0, score)


def get_quiz_recommendations(
    db: Session,
    student_id: int,
    engagement_level: str | None,
    limit: int = 3,
) -> List[dict]:
    """Returns recommended quizzes based on engagement level and past performance."""
    attempted_quiz_ids = {a.quiz_id for a in db.query(QuizAttempt).filter(
        QuizAttempt.student_id == student_id
    ).all()}

    all_quizzes = db.query(Quiz).filter(Quiz.is_active == True).all()

    if engagement_level == "Low":
        target = ["beginner"]
    elif engagement_level == "Medium":
        target = ["beginner", "intermediate"]
    else:
        target = ["intermediate", "advanced"]

    recs = []
    for quiz in all_quizzes:
        if quiz.id in attempted_quiz_ids:
            continue
        if quiz.difficulty not in target:
            continue
        recs.append({
            "quiz_id"   : quiz.id,
            "title"     : quiz.title,
            "topic"     : quiz.topic or quiz.module,
            "difficulty": quiz.difficulty,
            "reason"    : f"Try this quiz to test your understanding of {quiz.topic or quiz.module}.",
        })

    return recs[:limit]
