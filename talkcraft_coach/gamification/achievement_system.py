import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.models import User, Session, Achievement
from talkcraft_coach.gamification.badges import BADGE_DEFINITIONS
from talkcraft_coach.utils.logger import get_logger

logger = get_logger("achievement_system")


class AchievementSystem:
    def check_and_award(self, user_id: int, db: DbSession) -> List[Dict]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        unlocked_ids = {
            a.badge_id for a in db.query(Achievement).filter(Achievement.user_id == user_id).all()
        }

        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.ended_at.isnot(None),
        ).order_by(Session.started_at.desc()).all()

        if not sessions:
            return []

        context = self._build_context(user, sessions)
        new_achievements = []

        for badge in BADGE_DEFINITIONS:
            if badge["badge_id"] in unlocked_ids:
                continue
            if self._check_condition(badge["condition"], context):
                achievement = Achievement(
                    user_id=user_id,
                    badge_id=badge["badge_id"],
                    title=badge["title"],
                    description=badge["description"],
                    category=badge["category"],
                    icon=badge["icon"],
                    session_id=sessions[0].id if sessions else None,
                    progress_value=1.0,
                    progress_max=1.0,
                )
                db.add(achievement)
                db.commit()
                db.refresh(achievement)
                new_achievements.append({
                    "badge_id": badge["badge_id"],
                    "title": badge["title"],
                    "description": badge["description"],
                    "category": badge["category"],
                    "icon": badge["icon"],
                    "unlocked_at": achievement.unlocked_at.isoformat(),
                })
                logger.info(f"User {user_id} unlocked achievement: {badge['title']}")

        return new_achievements

    def get_user_achievements(self, user_id: int, db: DbSession) -> Dict:
        unlocked = db.query(Achievement).filter(
            Achievement.user_id == user_id,
        ).order_by(Achievement.unlocked_at.desc()).all()

        unlocked_ids = {a.badge_id for a in unlocked}

        all_badges = []
        for badge in BADGE_DEFINITIONS:
            match = next((a for a in unlocked if a.badge_id == badge["badge_id"]), None)
            all_badges.append({
                "badge_id": badge["badge_id"],
                "title": badge["title"],
                "description": badge["description"],
                "category": badge["category"],
                "icon": badge["icon"],
                "unlocked": badge["badge_id"] in unlocked_ids,
                "unlocked_at": match.unlocked_at.isoformat() if match else None,
            })

        categories = {}
        for badge in all_badges:
            cat = badge["category"]
            if cat not in categories:
                categories[cat] = {"unlocked": 0, "total": 0}
            categories[cat]["total"] += 1
            if badge["unlocked"]:
                categories[cat]["unlocked"] += 1

        return {
            "total_unlocked": len(unlocked),
            "total_available": len(BADGE_DEFINITIONS),
            "progress_pct": round((len(unlocked) / len(BADGE_DEFINITIONS)) * 100, 1) if BADGE_DEFINITIONS else 0,
            "categories": categories,
            "recent_unlocked": [
                {
                    "badge_id": a.badge_id,
                    "title": a.title,
                    "description": a.description,
                    "category": a.category,
                    "icon": a.icon,
                    "unlocked_at": a.unlocked_at.isoformat(),
                }
                for a in unlocked[:5]
            ],
            "badges": all_badges,
        }

    def _build_context(self, user: User, sessions: List[Session]) -> Dict:
        total_sessions = len(sessions)
        total_minutes = sum(s.duration_seconds or 0 for s in sessions) / 60
        modes_tried = len(set(s.mode for s in sessions if s.mode))
        topics_count = len(set(s.topic for s in sessions if s.topic))

        latest = sessions[0] if sessions else None
        best = max(sessions, key=lambda s: s.overall_score or 0) if sessions else None

        streak = 0
        if sessions and sessions[0].started_at:
            today = datetime.datetime.utcnow().date()
            yesterday = today - datetime.timedelta(days=1)
            dates = sorted(set(s.started_at.date() for s in sessions if s.started_at), reverse=True)
            if dates and (dates[0] == today or dates[0] == yesterday):
                streak = 1
                for i in range(len(dates) - 1):
                    if (dates[i] - dates[i + 1]).days == 1:
                        streak += 1
                    else:
                        break

        improving = 0
        if len(sessions) >= 2:
            for i in range(min(len(sessions) - 1, 4)):
                if (sessions[i].overall_score or 0) > (sessions[i + 1].overall_score or 0):
                    improving += 1
                else:
                    break

        all_high = latest and all([
            (latest.average_eye_contact or 0) >= 0.8,
            (latest.average_posture or 0) >= 0.8,
            (latest.confidence_score or 0) >= 0.8,
            (latest.engagement_score or 0) >= 0.8,
            (latest.clarity_score or 0) >= 0.8,
        ])

        best_ever = best.overall_score or 0 if best else 0
        worst = min(sessions, key=lambda s: s.overall_score or float('inf')) if sessions else None
        worst_score = worst.overall_score or 0 if worst else 0
        big_improvement = (best_ever - worst_score) >= 0.2 if best and worst else False

        interview_excellent = len([s for s in sessions if s.mode == "hr_interviewer" and (s.overall_score or 0) >= 0.8])
        speaking_excellent = len([s for s in sessions if s.mode == "public_speaking" and (s.overall_score or 0) >= 0.8])
        debate_excellent = len([s for s in sessions if s.mode == "debate_opponent" and (s.overall_score or 0) >= 0.8])

        return {
            "sessions_count": total_sessions,
            "practice_minutes": total_minutes,
            "streak_days": streak,
            "modes_tried": modes_tried,
            "topics_count": topics_count,
            "latest_session": latest,
            "best_session": best,
            "filler_rate": latest.filler_rate if latest else 1.0,
            "pace_ideal": 1 if latest and 140 <= (latest.average_wpm or 0) <= 170 else 0,
            "grammar_zero": 1 if latest and (latest.grammar_error_count or 0) == 0 else 0,
            "confidence_high": latest.confidence_score if latest else 0,
            "eye_contact_high": latest.average_eye_contact if latest else 0,
            "posture_high": latest.average_posture if latest else 0,
            "all_metrics_high": 1 if all_high else 0,
            "improving_sessions": improving,
            "big_improvement": 1 if big_improvement else 0,
            "interview_excellence": interview_excellent,
            "speaking_excellence": speaking_excellent,
            "debate_excellence": debate_excellent,
            "score_above_90": 1 if best_ever >= 0.9 else 0,
            "score_above_95": 1 if best_ever >= 0.95 else 0,
        }

    def _check_condition(self, condition: Dict, context: Dict) -> bool:
        cond_type = condition["type"]
        operator = condition["operator"]
        value = condition["value"]
        actual = context.get(cond_type, 0)

        if operator == ">=":
            return actual >= value
        elif operator == "<=":
            return actual <= value
        elif operator == ">":
            return actual > value
        elif operator == "<":
            return actual < value
        elif operator == "==":
            return actual == value
        return False
