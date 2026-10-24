"""
EngageAI Backend — routes/content.py
GET  /content/videos
GET  /content/videos/{id}
POST /content/videos/{id}/progress
POST /content/videos
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from backend.database import get_db
from backend.models.user import User
from backend.models.content import LearningContent, ContentProgress
from backend.models.activity import ActivityEvent
from backend.auth.dependencies import get_current_user, require_teacher

router = APIRouter(prefix="/content", tags=["Learning Content"])


class ProgressUpdateRequest(BaseModel):
    watch_seconds: int
    duration_seconds: Optional[int] = None
    is_completed: Optional[bool] = False


class ContentCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    module: str = "General"
    topic: Optional[str] = None
    content_type: str = "video"
    video_url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = 300
    difficulty: str = "beginner"
    tags: Optional[str] = None
    source_name: Optional[str] = None
    license_type: Optional[str] = None
    attribution: Optional[str] = None
    source_url: Optional[str] = None
    allow_embedding: Optional[bool] = True


@router.get("/videos")
def get_videos(
    module: Optional[str] = None,
    difficulty: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(LearningContent).filter(LearningContent.is_active == True)
    if module:
        query = query.filter(LearningContent.module == module)
    if difficulty:
        query = query.filter(LearningContent.difficulty == difficulty)

    videos = query.all()
    
    # Get user progress for each video
    progress_map = {
        p.content_id: p for p in db.query(ContentProgress).filter(ContentProgress.student_id == current_user.id).all()
    }

    res = []
    for v in videos:
        prog = progress_map.get(v.id)
        res.append({
            "id": v.id,
            "title": v.title,
            "description": v.description,
            "module": v.module,
            "topic": v.topic,
            "content_type": v.content_type,
            "video_url": v.video_url,
            "thumbnail_url": v.thumbnail_url,
            "duration_seconds": v.duration_seconds,
            "difficulty": v.difficulty,
            "tags": v.tags,
            "source_name": v.source_name,
            "license_type": v.license_type,
            "attribution": v.attribution,
            "source_url": v.source_url,
            "allow_embedding": v.allow_embedding,
            "concept_id": v.concept_id,
            "user_progress": {
                "watch_seconds": prog.watch_seconds if prog else 0,
                "completion_pct": prog.completion_pct if prog else 0.0,
                "is_completed": prog.is_completed if prog else False
            }
        })
    return res


@router.get("/videos/{video_id}")
def get_video_detail(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    video = db.query(LearningContent).filter(LearningContent.id == video_id, LearningContent.is_active == True).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

    prog = db.query(ContentProgress).filter(
        ContentProgress.student_id == current_user.id,
        ContentProgress.content_id == video_id
    ).first()

    return {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "module": video.module,
        "topic": video.topic,
        "content_type": video.content_type,
        "video_url": video.video_url,
        "thumbnail_url": video.thumbnail_url,
        "duration_seconds": video.duration_seconds,
        "difficulty": video.difficulty,
        "tags": video.tags,
        "source_name": video.source_name,
        "license_type": video.license_type,
        "attribution": video.attribution,
        "source_url": video.source_url,
        "allow_embedding": video.allow_embedding,
        "user_progress": {
            "watch_seconds": prog.watch_seconds if prog else 0,
            "completion_pct": prog.completion_pct if prog else 0.0,
            "is_completed": prog.is_completed if prog else False
        }
    }


@router.post("/videos/{video_id}/progress")
def update_video_progress(
    video_id: int,
    body: ProgressUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    video = db.query(LearningContent).filter(LearningContent.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video content not found.")

    duration = body.duration_seconds or video.duration_seconds or 300
    completion_pct = min(1.0, body.watch_seconds / float(duration)) if duration > 0 else 0.0
    is_completed = (completion_pct >= 0.85)

    prog = db.query(ContentProgress).filter(
        ContentProgress.student_id == current_user.id,
        ContentProgress.content_id == video_id
    ).first()

    if not prog:
        prog = ContentProgress(
            student_id=current_user.id,
            content_id=video_id,
            watch_seconds=body.watch_seconds,
            completion_pct=completion_pct,
            is_completed=is_completed,
            last_watched_at=datetime.utcnow()
        )
        db.add(prog)
    else:
        prog.watch_seconds = max(prog.watch_seconds, body.watch_seconds)
        prog.completion_pct = max(prog.completion_pct, completion_pct)
        if is_completed:
            prog.is_completed = True
        prog.last_watched_at = datetime.utcnow()

    # Track activity event for backend features
    event_type = "VIDEO_COMPLETED" if is_completed else "VIDEO_PROGRESS"
    activity = ActivityEvent(
        student_id=current_user.id,
        content_id=video_id,
        event_type=event_type,
        duration=body.watch_seconds,
        timestamp=datetime.utcnow()
    )
    db.add(activity)

    db.commit()
    db.refresh(prog)

    return {
        "status": "success",
        "watch_seconds": prog.watch_seconds,
        "completion_pct": prog.completion_pct,
        "is_completed": prog.is_completed
    }


@router.post("/videos", status_code=201)
def create_video_content(
    body: ContentCreateRequest,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    content = LearningContent(
        title=body.title,
        description=body.description,
        module=body.module,
        topic=body.topic,
        content_type=body.content_type,
        video_url=body.video_url,
        thumbnail_url=body.thumbnail_url,
        duration_seconds=body.duration_seconds,
        difficulty=body.difficulty,
        tags=body.tags,
        source_name=body.source_name,
        license_type=body.license_type,
        attribution=body.attribution,
        source_url=body.source_url,
        allow_embedding=body.allow_embedding,
        created_by=current_user.id,
        created_at=datetime.utcnow()
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return {"message": "Content created successfully", "content_id": content.id}


@router.put("/videos/{video_id}")
def update_video_content(
    video_id: int,
    body: ContentCreateRequest,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    content = db.query(LearningContent).filter(LearningContent.id == video_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Video not found")

    content.title = body.title
    content.description = body.description
    content.module = body.module
    content.topic = body.topic
    content.video_url = body.video_url
    content.thumbnail_url = body.thumbnail_url
    content.duration_seconds = body.duration_seconds
    content.difficulty = body.difficulty
    content.tags = body.tags
    content.source_name = body.source_name
    content.license_type = body.license_type
    content.attribution = body.attribution
    content.source_url = body.source_url
    content.allow_embedding = body.allow_embedding

    db.commit()
    return {"message": "Content updated successfully"}


@router.delete("/videos/{video_id}")
def delete_video_content(
    video_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    content = db.query(LearningContent).filter(LearningContent.id == video_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Video not found")

    content.is_active = False
    db.commit()
    return {"message": "Content deactivated successfully"}


@router.get("/videos/{video_id}/quizzes")
def get_video_quizzes(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from backend.models.quiz import Quiz, QuizAttempt
    quizzes = db.query(Quiz).filter(Quiz.video_id == video_id, Quiz.is_active == True).all()

    attempts = db.query(QuizAttempt).filter(QuizAttempt.student_id == current_user.id).all()
    attempts_map = {}
    for a in attempts:
        if a.quiz_id not in attempts_map or a.score_pct > attempts_map[a.quiz_id].score_pct:
            attempts_map[a.quiz_id] = a

    res = []
    for q in quizzes:
        att = attempts_map.get(q.id)
        res.append({
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "difficulty": q.difficulty,
            "question_count": len(q.questions),
            "user_attempt": {
                "attempted": att is not None,
                "best_score_pct": att.score_pct if att else 0.0,
                "last_attempted_at": att.completed_at.isoformat() if att and att.completed_at else None
            }
        })
    return res
