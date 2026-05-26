from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession
from talkcraft_enterprise.database.database import get_db
from talkcraft_enterprise.behavioral.intelligence import behavioral_intelligence

router = APIRouter(prefix="/api/behavioral", tags=["behavioral"])


@router.post("/analyze")
async def analyze_patterns(sessions: list):
    return behavioral_intelligence.analyze_patterns(sessions)


@router.post("/sentiment")
async def analyze_sentiment(sessions: list):
    return behavioral_intelligence.analyze_sentiment_trend(sessions)


@router.get("/profile/{user_id}")
async def get_profile(user_id: int, db: DbSession = Depends(get_db)):
    return behavioral_intelligence.generate_behavioral_report(user_id, db)


@router.get("/patterns")
async def get_patterns():
    from talkcraft_enterprise.behavioral.intelligence import COMMUNICATION_PATTERNS
    return {"patterns": [{"id": k, **v} for k, v in COMMUNICATION_PATTERNS.items()]}
