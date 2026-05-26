import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.database import get_db
from talkcraft_coach.database.models import User, Session as SessionModel
from talkcraft_coach.auth.auth_middleware import require_auth, optional_auth
from talkcraft_coach.analytics.session_analyzer import SessionAnalyzer
from talkcraft_coach.gamification.achievement_system import AchievementSystem

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
session_analyzer = SessionAnalyzer()
achievement_system = AchievementSystem()


class SessionCreateRequest(BaseModel):
    session_type: str = "mic"
    mode: str = "casual_conversation"
    topic: str = ""
    difficulty: str = "intermediate"
    duration_seconds: int = 0
    overall_score: float = 0.0
    word_count: int = 0
    filler_count: int = 0
    filler_rate: float = 0.0
    grammar_error_count: int = 0
    average_wpm: float = 0.0
    pace_consistency: float = 0.0
    average_eye_contact: float = 0.0
    average_posture: float = 0.0
    average_hand_activity: float = 0.0
    confidence_score: float = 0.0
    engagement_score: float = 0.0
    clarity_score: float = 0.0
    transcript_text: str = ""
    ai_summary: str = ""
    weakness_tags: list = []
    strength_tags: list = []
    metadata_json: dict = {}


@router.post("/create")
async def create_session(
    req: SessionCreateRequest,
    user_data: dict = Depends(require_auth),
    db: DbSession = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_data["user_id"]).first()

    session = SessionModel(
        user_id=user_data["user_id"],
        session_type=req.session_type,
        mode=req.mode,
        topic=req.topic,
        difficulty=req.difficulty,
        duration_seconds=req.duration_seconds,
        overall_score=req.overall_score,
        word_count=req.word_count,
        filler_count=req.filler_count,
        filler_rate=req.filler_rate,
        grammar_error_count=req.grammar_error_count,
        average_wpm=req.average_wpm,
        pace_consistency=req.pace_consistency,
        average_eye_contact=req.average_eye_contact,
        average_posture=req.average_posture,
        average_hand_activity=req.average_hand_activity,
        confidence_score=req.confidence_score,
        engagement_score=req.engagement_score,
        clarity_score=req.clarity_score,
        transcript_text=req.transcript_text,
        ai_summary=req.ai_summary,
        weakness_tags=req.weakness_tags,
        strength_tags=req.strength_tags,
        metadata_json=req.metadata_json,
        ended_at=datetime.datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    if user:
        user.total_sessions = (user.total_sessions or 0) + 1
        user.total_practice_time_minutes = (user.total_practice_time_minutes or 0) + (req.duration_seconds // 60)
        db.commit()

    new_achievements = achievement_system.check_and_award(user_data["user_id"], db)

    return {
        "session_id": session.id,
        "analysis": session_analyzer.analyze_session(session),
        "new_achievements": new_achievements,
    }


@router.get("/{session_id}")
async def get_session(
    session_id: int,
    user_data: dict = Depends(require_auth),
    db: DbSession = Depends(get_db),
):
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == user_data["user_id"],
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_analyzer.analyze_session(session)
