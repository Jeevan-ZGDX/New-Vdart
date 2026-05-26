import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Optional
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.models import Session
from talkcraft_coach.utils.logger import get_logger
from talkcraft_coach.utils.config import config

logger = get_logger("weakness_detector")


class WeaknessDetector:
    def detect_weaknesses(self, user_id: int, db: DbSession, days: int = 30) -> Dict:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.started_at >= cutoff,
            Session.ended_at.isnot(None),
        ).order_by(Session.started_at.desc()).limit(50).all()

        if not sessions:
            return {"available": False, "message": "No sessions found"}

        metric_scores = defaultdict(list)
        for s in sessions:
            metrics = {
                "filler_words": 1.0 - min(1.0, (s.filler_rate or 0) * 5),
                "speaking_pace": self._pace_score(s.average_wpm or 0),
                "grammar": 1.0 - min(1.0, (s.grammar_error_count or 0) / max(1, (s.word_count or 1)) * 15),
                "eye_contact": s.average_eye_contact or 0,
                "posture": s.average_posture or 0,
                "confidence": s.confidence_score or 0,
                "engagement": s.engagement_score or 0,
                "clarity": s.clarity_score or 0,
                "pace_consistency": s.pace_consistency or 0.5,
            }
            for k, v in metrics.items():
                metric_scores[k].append(v)

        weaknesses = []
        strengths = []
        threshold = config.analytics.weakness_detection_threshold

        for metric, scores in metric_scores.items():
            avg_score = sum(scores) / len(scores)
            trend = self._compute_trend(scores)
            status = "critical" if avg_score < 0.3 else ("weak" if avg_score < threshold else "fair" if avg_score < 0.8 else "strong")

            entry = {
                "area": metric,
                "label": metric.replace("_", " ").title(),
                "average_score": round(avg_score, 2),
                "latest_score": round(scores[0], 2),
                "trend": trend,
                "status": status,
                "sessions_analyzed": len(scores),
            }

            if status == "strong":
                strengths.append(entry)
            else:
                weaknesses.append(entry)

        weaknesses.sort(key=lambda x: x["average_score"])

        primary = weaknesses[:3] if weaknesses else []
        areas = [w["area"] for w in primary]

        return {
            "available": True,
            "sessions_analyzed": len(sessions),
            "period_days": days,
            "weaknesses": weaknesses,
            "strengths": strengths,
            "primary_focus_areas": areas,
            "overall_weakness_score": round(
                sum(w["average_score"] for w in weaknesses) / len(weaknesses), 2
            ) if weaknesses else 1.0,
        }

    def _pace_score(self, wpm: float) -> float:
        if 140 <= wpm <= 170:
            return 1.0
        if 120 <= wpm <= 190:
            return 0.8
        if 100 <= wpm <= 210:
            return 0.6
        if wpm > 0:
            return 0.3
        return 0.0

    def _compute_trend(self, scores: List[float]) -> str:
        if len(scores) < 3:
            return "stable"
        recent = scores[:len(scores)//3]
        older = scores[-len(scores)//3:]
        avg_recent = sum(recent) / len(recent)
        avg_older = sum(older) / len(older)
        diff = avg_recent - avg_older
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        return "stable"
