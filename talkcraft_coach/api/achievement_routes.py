from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.database import get_db
from talkcraft_coach.auth.auth_middleware import require_auth
from talkcraft_coach.gamification.achievement_system import AchievementSystem

router = APIRouter(prefix="/api/achievements", tags=["achievements"])
achievement_system = AchievementSystem()


@router.get("")
async def get_achievements(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    return achievement_system.get_user_achievements(user_data["user_id"], db)


@router.post("/check")
async def check_achievements(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    new = achievement_system.check_and_award(user_data["user_id"], db)
    return {"new_achievements": new, "count": len(new)}
