from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.database import get_db
from talkcraft_coach.auth.auth_middleware import require_auth
from talkcraft_coach.analytics.progress_analyzer import ProgressAnalyzer
from talkcraft_coach.analytics.weakness_detector import WeaknessDetector
from talkcraft_coach.analytics.trend_analyzer import TrendAnalyzer
from talkcraft_coach.coaching.adaptive_coach import AdaptiveCoach
from talkcraft_coach.coaching.improvement_planner import ImprovementPlanner
from talkcraft_coach.coaching.practice_recommender import PracticeRecommender
from talkcraft_coach.gamification.achievement_system import AchievementSystem

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

progress_analyzer = ProgressAnalyzer()
weakness_detector = WeaknessDetector()
trend_analyzer = TrendAnalyzer()
adaptive_coach = AdaptiveCoach()
improvement_planner = ImprovementPlanner()
practice_recommender = PracticeRecommender()
achievement_system = AchievementSystem()


@router.get("/overview")
async def get_dashboard_overview(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    uid = user_data["user_id"]

    summary = progress_analyzer.get_user_summary(uid, db)
    weekly = progress_analyzer.get_weekly_summary(uid, db)
    weaknesses = weakness_detector.detect_weaknesses(uid, db)
    trends = trend_analyzer.compute_trends(uid, db)
    coaching_focus = adaptive_coach.get_coaching_focus(uid, db)
    plan = improvement_planner.get_active_plan(uid, db)
    recommendations = practice_recommender.get_todays_recommendations(uid, db)
    achievements = achievement_system.get_user_achievements(uid, db)

    weekly_progress = progress_analyzer.compute_weekly_progress(uid, db)

    return {
        "summary": summary,
        "weekly": weekly,
        "weaknesses": weaknesses,
        "trends": trends,
        "coaching_focus": coaching_focus,
        "improvement_plan": plan,
        "daily_recommendations": recommendations,
        "achievements": achievements,
        "weekly_progress_chart": weekly_progress,
    }
