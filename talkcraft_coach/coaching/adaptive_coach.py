import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.models import User, Session
from talkcraft_coach.utils.logger import get_logger
from talkcraft_coach.utils.config import config

logger = get_logger("adaptive_coach")


class AdaptiveCoach:
    def determine_difficulty(self, user_id: int, db: DbSession) -> Dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"level": "beginner", "reason": "New user"}

        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.ended_at.isnot(None),
        ).order_by(Session.started_at.desc()).limit(20).all()

        if len(sessions) < config.coaching.improvement_detection_min_sessions:
            return {
                "level": user.skill_level or "beginner",
                "reason": "Not enough sessions to adapt",
                "sessions_analyzed": len(sessions),
            }

        recent_scores = [s.overall_score or 0 for s in sessions[:5]]
        avg_recent = sum(recent_scores) / len(recent_scores)
        all_scores = [s.overall_score or 0 for s in sessions]
        avg_all = sum(all_scores) / len(all_scores)

        current_level = user.skill_level or "beginner"
        new_level = current_level
        reasons = []

        if avg_recent >= config.coaching.advanced_threshold:
            if current_level in ("beginner", "intermediate"):
                new_level = "advanced"
                reasons.append(f"Consistently scoring above {config.coaching.advanced_threshold*100:.0f}%")
        elif avg_recent >= config.coaching.intermediate_threshold:
            if current_level == "beginner":
                new_level = "intermediate"
                reasons.append(f"Scoring above {config.coaching.intermediate_threshold*100:.0f}%")
            elif current_level == "advanced":
                new_level = "intermediate"
                reasons.append("Recent scores dropped below advanced threshold")
        elif avg_recent < config.coaching.beginner_threshold:
            if current_level in ("intermediate", "advanced"):
                new_level = "beginner"
                reasons.append(f"Scoring below {config.coaching.beginner_threshold*100:.0f}%")

        trend = "improving" if avg_recent > avg_all else ("declining" if avg_recent < avg_all else "stable")

        if new_level != current_level and user.skill_level != new_level:
            user.skill_level = new_level
            db.commit()
            logger.info(f"User {user_id} difficulty adapted: {current_level} -> {new_level}")

        return {
            "level": new_level,
            "previous_level": current_level,
            "changed": new_level != current_level,
            "reason": "; ".join(reasons) if reasons else "Maintaining current level",
            "trend": trend,
            "avg_recent_score": round(avg_recent, 2),
            "avg_all_time_score": round(avg_all, 2),
            "sessions_analyzed": len(sessions),
        }

    def get_coaching_focus(self, user_id: int, db: DbSession) -> Dict:
        from talkcraft_coach.analytics.weakness_detector import WeaknessDetector
        detector = WeaknessDetector()
        weaknesses = detector.detect_weaknesses(user_id, db)
        difficulty = self.determine_difficulty(user_id, db)

        focus_areas = []
        for w in weaknesses.get("weaknesses", []):
            if w.get("status") in ("weak", "critical"):
                focus_areas.append(w["area"])

        level = difficulty["level"]
        coaching_style_map = {
            "beginner": {
                "style": "supportive",
                "complexity": "simple",
                "feedback_frequency": "frequent",
                "encouragement": "high",
                "description": "Focus on building foundational skills with gentle guidance",
            },
            "intermediate": {
                "style": "constructive",
                "complexity": "moderate",
                "feedback_frequency": "balanced",
                "encouragement": "moderate",
                "description": "Mix of encouragement and constructive improvement areas",
            },
            "advanced": {
                "style": "challenging",
                "complexity": "complex",
                "feedback_frequency": "targeted",
                "encouragement": "low",
                "description": "Focus on refinement, nuance, and advanced techniques",
            },
        }

        return {
            "difficulty": level,
            "coaching_style": coaching_style_map.get(level, coaching_style_map["beginner"]),
            "focus_areas": focus_areas[:3],
            "trend": difficulty.get("trend", "stable"),
            "recommended_mode": self._recommend_mode(focus_areas, level),
        }

    def _recommend_mode(self, focus_areas: List[str], level: str) -> Dict:
        mode_map = {
            "filler_words": {
                "mode": "casual_conversation",
                "reason": "Casual conversation helps reduce filler word usage naturally",
            },
            "speaking_pace": {
                "mode": "public_speaking",
                "reason": "Public speaking mode with pace feedback",
            },
            "grammar": {
                "mode": "presentation_evaluator",
                "reason": "Structured presentation practice for grammar improvement",
            },
            "eye_contact": {
                "mode": "casual_conversation",
                "reason": "Conversation practice to build eye contact habits",
            },
            "posture": {
                "mode": "presentation_evaluator",
                "reason": "Presentation mode encourages better posture awareness",
            },
            "confidence": {
                "mode": "public_speaking",
                "reason": "Public speaking builds confidence through practice",
            },
            "engagement": {
                "mode": "hr_interviewer",
                "reason": "Interview practice improves engagement and responsiveness",
            },
            "clarity": {
                "mode": "presentation_evaluator",
                "reason": "Presentation mode with emphasis on clear communication",
            },
        }

        if not focus_areas:
            return {"mode": "casual_conversation", "reason": "General practice"}

        for area in focus_areas:
            if area in mode_map:
                return mode_map[area]

        return {"mode": "casual_conversation", "reason": "Recommended for general improvement"}

    def adapt_conversation_parameters(self, user_id: int, db: DbSession) -> Dict:
        difficulty = self.determine_difficulty(user_id, db)
        level = difficulty["level"]

        params = {
            "beginner": {
                "temperature": 0.8,
                "max_tokens": 150,
                "topic_complexity": "simple",
                "response_length": "short",
                "question_style": "direct",
                "feedback_detail": "high",
            },
            "intermediate": {
                "temperature": 0.7,
                "max_tokens": 200,
                "topic_complexity": "moderate",
                "response_length": "moderate",
                "question_style": "open_ended",
                "feedback_detail": "moderate",
            },
            "advanced": {
                "temperature": 0.6,
                "max_tokens": 300,
                "topic_complexity": "complex",
                "response_length": "detailed",
                "question_style": "challenging",
                "feedback_detail": "targeted",
            },
        }

        return params.get(level, params["beginner"])
