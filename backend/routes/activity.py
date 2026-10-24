"""
EngageAI Backend — routes/activity.py
POST /activity/events
GET  /activity/events
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from backend.database import get_db
from backend.models.user import User
from backend.models.activity import ActivityEvent
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix="/activity", tags=["Activity Tracking"])


class EventItem(BaseModel):
    event_type: str
    content_id: Optional[int] = None
    quiz_id: Optional[int] = None
    duration: Optional[int] = None
    week_index: Optional[int] = None
    metadata_json: Optional[str] = None


class BatchEventsRequest(BaseModel):
    events: List[EventItem]


@router.post("/events")
def track_batch_events(
    body: BatchEventsRequest,
    db: Session = Depends(get_db),
    # Standard bearer-token auth (normal fetch requests)
    current_user: User = Depends(get_current_user),
):
    if not body.events:
        return {"status": "success", "processed_count": 0}

    new_records = []
    now = datetime.utcnow()
    for ev in body.events:
        record = ActivityEvent(
            student_id=current_user.id,
            content_id=ev.content_id,
            quiz_id=ev.quiz_id,
            event_type=ev.event_type,
            duration=ev.duration,
            week_index=ev.week_index,
            metadata_json=ev.metadata_json,
            timestamp=now
        )
        new_records.append(record)

    db.bulk_save_objects(new_records)
    db.commit()

    return {
        "status": "success",
        "processed_count": len(new_records)
    }


@router.post("/events/beacon")
def track_beacon_events(
    body: BatchEventsRequest,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Dedicated endpoint for navigator.sendBeacon page-exit flushes.
    sendBeacon cannot set custom headers, so the JWT token is passed
    as a ?token= query parameter instead.
    """
    from backend.auth.jwt import decode_access_token
    from backend.models.user import User as UserModel

    if not token:
        raise HTTPException(status_code=401, detail="Token required for beacon endpoint.")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    user_id = payload.get("sub")
    user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found.")

    if not body.events:
        return {"status": "success", "processed_count": 0}

    now = datetime.utcnow()
    new_records = []
    for ev in body.events:
        record = ActivityEvent(
            student_id=user.id,
            content_id=ev.content_id,
            quiz_id=ev.quiz_id,
            event_type=ev.event_type,
            duration=ev.duration,
            week_index=ev.week_index,
            metadata_json=ev.metadata_json,
            timestamp=now
        )
        new_records.append(record)

    db.bulk_save_objects(new_records)
    db.commit()

    return {"status": "success", "processed_count": len(new_records)}


@router.get("/events")
def get_user_events(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    events = db.query(ActivityEvent).filter(
        ActivityEvent.student_id == current_user.id
    ).order_by(ActivityEvent.timestamp.desc()).limit(limit).all()

    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "content_id": e.content_id,
            "quiz_id": e.quiz_id,
            "duration": e.duration,
            "timestamp": e.timestamp.isoformat()
        }
        for e in events
    ]
