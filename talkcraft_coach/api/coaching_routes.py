from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.database import get_db
from talkcraft_coach.auth.auth_middleware import require_auth
from talkcraft_coach.coaching.adaptive_coach import AdaptiveCoach
from talkcraft_coach.coaching.improvement_planner import ImprovementPlanner
from talkcraft_coach.coaching.practice_recommender import PracticeRecommender
from talkcraft_coach.coaching.topic_paths import TopicPaths

router = APIRouter(prefix="/api/coaching", tags=["coaching"])

adaptive_coach = AdaptiveCoach()
improvement_planner = ImprovementPlanner()
practice_recommender = PracticeRecommender()
topic_paths = TopicPaths()


@router.get("/difficulty")
async def get_difficulty(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    return adaptive_coach.determine_difficulty(user_data["user_id"], db)


@router.get("/focus")
async def get_coaching_focus(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    return adaptive_coach.get_coaching_focus(user_data["user_id"], db)


@router.get("/parameters")
async def get_conversation_parameters(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    return adaptive_coach.adapt_conversation_parameters(user_data["user_id"], db)


@router.get("/plan")
async def get_improvement_plan(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    plan = improvement_planner.get_active_plan(user_data["user_id"], db)
    if plan:
        return plan
    return improvement_planner.generate_plan(user_data["user_id"], db)


@router.post("/plan/generate")
async def generate_plan(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    return improvement_planner.regenerate_plan(user_data["user_id"], db)


@router.post("/plan/{plan_id}/complete")
async def complete_plan(plan_id: int, user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    success = improvement_planner.complete_plan(plan_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"status": "completed"}


@router.get("/recommendations")
async def get_recommendations(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    return practice_recommender.get_todays_recommendations(user_data["user_id"], db)


@router.post("/recommendations/generate")
async def generate_recommendations(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    return practice_recommender.generate_daily_recommendations(user_data["user_id"], db)


@router.post("/recommendations/{rec_id}/complete")
async def complete_recommendation(
    rec_id: int,
    user_data: dict = Depends(require_auth),
    db: DbSession = Depends(get_db),
):
    success = practice_recommender.mark_completed(rec_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"status": "completed"}


@router.get("/paths")
async def get_learning_paths():
    return topic_paths.get_all_paths()


@router.get("/paths/{path_id}")
async def get_learning_path(path_id: str):
    path = topic_paths.get_path(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    return path
