import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession
from talkcraft_enterprise.database.database import get_db
from talkcraft_enterprise.database.models import SessionRecording, CollaborativeRoom

router = APIRouter(prefix="/api/recordings", tags=["recordings"])


@router.post("/save")
async def save_recording(
    user_id: int, session_type: str, duration_seconds: int = 0,
    room_id: Optional[int] = None, transcript_full: str = "",
    metrics_snapshot: dict = {}, recording_data: dict = {},
    db: DbSession = Depends(get_db),
):
    recording = SessionRecording(
        room_id=room_id,
        user_id=user_id,
        session_type=session_type,
        duration_seconds=duration_seconds,
        recording_data=recording_data,
        transcript_full=transcript_full,
        metrics_snapshot=metrics_snapshot,
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)
    return {"recording_id": recording.id, "status": "saved"}


@router.get("/user/{user_id}")
async def get_user_recordings(user_id: int, limit: int = 20, db: DbSession = Depends(get_db)):
    recordings = db.query(SessionRecording).filter(
        SessionRecording.user_id == user_id
    ).order_by(SessionRecording.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "session_type": r.session_type,
            "duration_seconds": r.duration_seconds,
            "created_at": r.created_at.isoformat(),
        }
        for r in recordings
    ]


@router.get("/{recording_id}")
async def get_recording(recording_id: int, db: DbSession = Depends(get_db)):
    recording = db.query(SessionRecording).filter(SessionRecording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return {
        "id": recording.id,
        "room_id": recording.room_id,
        "user_id": recording.user_id,
        "session_type": recording.session_type,
        "duration_seconds": recording.duration_seconds,
        "recording_data": recording.recording_data,
        "transcript_full": recording.transcript_full,
        "metrics_snapshot": recording.metrics_snapshot,
        "created_at": recording.created_at.isoformat(),
    }


@router.delete("/{recording_id}")
async def delete_recording(recording_id: int, db: DbSession = Depends(get_db)):
    recording = db.query(SessionRecording).filter(SessionRecording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    db.delete(recording)
    db.commit()
    return {"status": "deleted"}
