from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession
from talkcraft_enterprise.database.database import get_db
from talkcraft_enterprise.enterprise.team_analytics import team_analytics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/enterprise/{org_id}")
async def get_enterprise_dashboard(org_id: int, db: DbSession = Depends(get_db)):
    return team_analytics.get_organization_overview(org_id, db)


@router.get("/team/{team_id}")
async def get_team_dashboard(team_id: int, db: DbSession = Depends(get_db)):
    return team_analytics.get_team_dashboard(team_id, db)


@router.get("/features")
async def get_features():
    return {
        "features": {
            "multilingual": {"enabled": True, "languages": ["en", "hi", "ta", "es", "fr"]},
            "avatars": {"enabled": True, "avatars": ["coach", "interviewer", "audience", "debater", "evaluator", "partner"]},
            "collaboration": {"enabled": True, "max_participants": 10},
            "enterprise": {"enabled": True, "max_teams": 50},
            "certification": {"enabled": True, "levels": ["bronze", "silver", "gold", "platinum"]},
            "benchmarking": {"enabled": True, "categories": 7, "roles": 6},
            "role_training": {"enabled": True, "roles": 6, "scenarios": 10},
            "recruiter_simulator": {"enabled": True, "interview_types": 5, "personas": 4},
        },
        "version": "5.0.0",
    }
