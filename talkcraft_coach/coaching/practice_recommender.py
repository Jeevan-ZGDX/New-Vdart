import datetime
import random
from typing import Dict, List, Optional
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.models import User, Session, DailyRecommendation
from talkcraft_coach.utils.logger import get_logger
from talkcraft_coach.utils.config import config

logger = get_logger("practice_recommender")


class PracticeRecommender:
    def generate_daily_recommendations(self, user_id: int, db: DbSession) -> List[Dict]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return self._default_recommendations()

        today = datetime.datetime.utcnow().date()
        existing = db.query(DailyRecommendation).filter(
            DailyRecommendation.user_id == user_id,
            DailyRecommendation.date >= datetime.datetime(today.year, today.month, today.day),
        ).count()

        if existing > 0:
            return self.get_todays_recommendations(user_id, db)

        from talkcraft_coach.analytics.weakness_detector import WeaknessDetector
        from talkcraft_coach.coaching.adaptive_coach import AdaptiveCoach

        detector = WeaknessDetector()
        coach = AdaptiveCoach()

        weaknesses = detector.detect_weaknesses(user_id, db)
        difficulty = coach.determine_difficulty(user_id, db)
        level = difficulty["level"]

        focus_areas = [w["area"] for w in weaknesses.get("weaknesses", []) if w.get("status") in ("weak", "critical")]

        recs = []
        used_areas = set()

        if focus_areas:
            primary = focus_areas[0]
            used_areas.add(primary)
            recs.append(self._build_recommendation(
                user_id, primary, level, db,
                priority="high",
            ))

        if len(focus_areas) > 1:
            secondary = focus_areas[1]
            used_areas.add(secondary)
            recs.append(self._build_recommendation(
                user_id, secondary, level, db,
                priority="medium",
            ))

        all_areas = ["filler_words", "speaking_pace", "grammar", "eye_contact", "posture", "confidence", "engagement", "clarity"]
        remaining = [a for a in all_areas if a not in used_areas]
        if remaining:
            general = random.choice(remaining)
            recs.append(self._build_recommendation(
                user_id, general, level, db,
                priority="low",
                rec_type="general",
            ))

        while len(recs) < 3:
            area = random.choice(all_areas)
            if area not in used_areas:
                recs.append(self._build_recommendation(
                    user_id, area, level, db,
                    priority="low",
                    rec_type="general",
                ))
                used_areas.add(area)

        for r in recs:
            db.add(r)
        db.commit()

        return [self._rec_to_dict(r) for r in recs]

    def get_todays_recommendations(self, user_id: int, db: DbSession) -> List[Dict]:
        today = datetime.datetime.utcnow().date()
        recs = db.query(DailyRecommendation).filter(
            DailyRecommendation.user_id == user_id,
            DailyRecommendation.date >= datetime.datetime(today.year, today.month, today.day),
        ).all()
        if not recs:
            return self.generate_daily_recommendations(user_id, db)
        return [self._rec_to_dict(r) for r in recs]

    def mark_completed(self, rec_id: int, db: DbSession) -> bool:
        rec = db.query(DailyRecommendation).filter(DailyRecommendation.id == rec_id).first()
        if rec:
            rec.completed = True
            rec.completed_at = datetime.datetime.utcnow()
            db.commit()
            return True
        return False

    def _build_recommendation(self, user_id: int, area: str, level: str, db: DbSession,
                              priority: str = "medium", rec_type: str = "practice") -> DailyRecommendation:
        area_exercises = {
            "filler_words": {"title": "Filler Word Free Talk", "description": "Speak for 3 minutes without using any filler words (um, uh, like, you know). Take a silent pause instead.", "duration": 10},
            "speaking_pace": {"title": "Pace Control Practice", "description": "Practice speaking at 140-160 WPM. Use TalkCraft's real-time pace monitoring.", "duration": 5},
            "grammar": {"title": "Grammar Focus Session", "description": "Practice constructing grammatically correct responses. Focus on subject-verb agreement and tenses.", "duration": 10},
            "eye_contact": {"title": "Eye Contact Drill", "description": "Practice maintaining eye contact with the camera for 30-second intervals.", "duration": 5},
            "posture": {"title": "Posture Awareness Session", "description": "Practice speaking with proper posture: shoulders back, spine straight, chin level.", "duration": 5},
            "confidence": {"title": "Confidence Building Practice", "description": "Practice power poses and positive affirmations before your TalkCraft session.", "duration": 5},
            "engagement": {"title": "Active Engagement Drill", "description": "Practice asking follow-up questions and showing engagement in conversation.", "duration": 10},
            "clarity": {"title": "Clear Communication Practice", "description": "Practice explaining complex ideas in simple terms. Use the 'explain like I'm 10' technique.", "duration": 10},
        }
        mode_recommendations = {
            "filler_words": "casual_conversation",
            "speaking_pace": "public_speaking",
            "grammar": "presentation_evaluator",
            "eye_contact": "casual_conversation",
            "posture": "presentation_evaluator",
            "confidence": "public_speaking",
            "engagement": "hr_interviewer",
            "clarity": "presentation_evaluator",
        }

        info = area_exercises.get(area, area_exercises["confidence"])
        return DailyRecommendation(
            user_id=user_id,
            date=datetime.datetime.utcnow(),
            recommendation_type=rec_type,
            title=info["title"],
            description=f"{info['description']} Recommended mode: {mode_recommendations.get(area, 'casual_conversation')}.",
            duration_minutes=info["duration"],
            difficulty=level,
            focus_area=area,
            completed=False,
        )

    def _default_recommendations(self) -> List[Dict]:
        today = datetime.datetime.utcnow()
        return [
            {"date": today.isoformat(), "title": "Getting Started Practice", "description": "Start your first TalkCraft session. Try casual conversation mode to begin building your communication skills.", "duration_minutes": 10, "difficulty": "beginner", "focus_area": "general"},
            {"date": today.isoformat(), "title": "Filler Word Awareness", "description": "Practice speaking for 2 minutes without filler words. Count how many you catch yourself using.", "duration_minutes": 5, "difficulty": "beginner", "focus_area": "filler_words"},
            {"date": today.isoformat(), "title": "Paced Practice", "description": "Try reading a passage aloud at a comfortable pace. Focus on clarity over speed.", "duration_minutes": 5, "difficulty": "beginner", "focus_area": "speaking_pace"},
        ]

    def _rec_to_dict(self, rec: DailyRecommendation) -> Dict:
        return {
            "id": rec.id,
            "title": rec.title,
            "description": rec.description,
            "type": rec.recommendation_type,
            "duration_minutes": rec.duration_minutes,
            "difficulty": rec.difficulty,
            "focus_area": rec.focus_area,
            "completed": rec.completed,
            "date": rec.date.isoformat() if rec.date else "",
        }
