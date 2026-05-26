from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession
from talkcraft_enterprise.database.database import get_db
from talkcraft_enterprise.enterprise.team_analytics import team_analytics

router = APIRouter(prefix="/api/enterprise", tags=["enterprise"])


@router.get("/teams/{team_id}/dashboard")
async def get_team_dashboard(team_id: int, db: DbSession = Depends(get_db)):
    return team_analytics.get_team_dashboard(team_id, db)


@router.get("/organizations/{org_id}/overview")
async def get_org_overview(org_id: int, db: DbSession = Depends(get_db)):
    return team_analytics.get_organization_overview(org_id, db)


@router.get("/users/{user_id}/growth")
async def get_user_growth(user_id: int, db: DbSession = Depends(get_db)):
    return team_analytics.get_user_growth_metrics(user_id, db)


@router.get("/teams/{team_id}/growth")
async def get_team_growth(team_id: int, db: DbSession = Depends(get_db)):
    return team_analytics.get_communication_growth(team_id, db)
