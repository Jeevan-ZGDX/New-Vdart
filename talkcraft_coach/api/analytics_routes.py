from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.database import get_db
from talkcraft_coach.database.models import Session as SessionModel
from talkcraft_coach.auth.auth_middleware import require_auth
from talkcraft_coach.analytics.progress_analyzer import ProgressAnalyzer
from talkcraft_coach.analytics.trend_analyzer import TrendAnalyzer
from talkcraft_coach.analytics.weakness_detector import WeaknessDetector
from talkcraft_coach.analytics.session_analyzer import SessionAnalyzer

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
progress_analyzer = ProgressAnalyzer()
trend_analyzer = TrendAnalyzer()
weakness_detector = WeaknessDetector()
session_analyzer = SessionAnalyzer()


@router.get("/summary")
async def get_summary(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    return progress_analyzer.get_user_summary(user_data["user_id"], db)


@router.get("/weekly")
async def get_weekly(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    return progress_analyzer.get_weekly_summary(user_data["user_id"], db)


@router.get("/weekly-progress")
async def get_weekly_progress(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    return progress_analyzer.compute_weekly_progress(user_data["user_id"], db)


@router.get("/trends")
async def get_trends(
    days: int = Query(default=30, ge=1, le=365),
    user_data: dict = Depends(require_auth),
    db: DbSession = Depends(get_db),
):
    return trend_analyzer.compute_trends(user_data["user_id"], db, days)


@router.get("/trends/{metric}")
async def get_metric_trend(
    metric: str,
    days: int = Query(default=30, ge=1, le=365),
    user_data: dict = Depends(require_auth),
    db: DbSession = Depends(get_db),
):
    return trend_analyzer.get_metric_history(user_data["user_id"], db, metric, days)


@router.get("/weaknesses")
async def get_weaknesses(
    days: int = Query(default=30, ge=1, le=365),
    user_data: dict = Depends(require_auth),
    db: DbSession = Depends(get_db),
):
    return weakness_detector.detect_weaknesses(user_data["user_id"], db, days)


@router.get("/grammar")
async def get_grammar_improvement(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    return progress_analyzer.get_grammar_improvement(user_data["user_id"], db)


@router.get("/sessions")
async def get_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_data: dict = Depends(require_auth),
    db: DbSession = Depends(get_db),
):
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == user_data["user_id"],
        SessionModel.ended_at.isnot(None),
    ).order_by(SessionModel.started_at.desc()).offset(offset).limit(limit).all()

    return [
        session_analyzer.analyze_session(s) for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: int,
    user_data: dict = Depends(require_auth),
    db: DbSession = Depends(get_db),
):
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == user_data["user_id"],
    ).first()
    if not session:
        return {"error": "Session not found"}
    return session_analyzer.analyze_session(session)
