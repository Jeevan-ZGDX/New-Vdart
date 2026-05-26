import datetime
from collections import defaultdict
from typing import Dict, List, Optional
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.models import Session, Progress
from talkcraft_coach.utils.logger import get_logger
from talkcraft_coach.utils.config import config

logger = get_logger("trend_analyzer")


class TrendAnalyzer:
    METRICS = [
        "overall_score", "average_wpm", "filler_rate", "grammar_error_rate",
        "average_eye_contact", "average_posture", "confidence_score",
        "engagement_score", "clarity_score", "pace_consistency",
    ]

    def compute_trends(self, user_id: int, db: DbSession, days: int = None) -> Dict:
        window = days or config.analytics.trend_window_days
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=window)
        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.started_at >= cutoff,
            Session.ended_at.isnot(None),
        ).order_by(Session.started_at.asc()).all()

        if not sessions:
            return {"available": False, "message": "Not enough data"}

        trends = {}
        for metric in self.METRICS:
            metric_trend = self._compute_metric_trend(sessions, metric)
            if metric_trend:
                trends[metric] = metric_trend

        return {
            "available": True,
            "window_days": window,
            "session_count": len(sessions),
            "date_range": {
                "start": sessions[0].started_at.isoformat() if sessions[0].started_at else "",
                "end": sessions[-1].started_at.isoformat() if sessions[-1].started_at else "",
            },
            "trends": trends,
            "direction_summary": self._summarize_directions(trends),
            "weekly_averages": self._compute_weekly_averages(sessions),
        }

    def _compute_metric_trend(self, sessions: List[Session], metric: str) -> Optional[Dict]:
        values = []
        for s in sessions:
            v = self._get_metric_value(s, metric)
            if v is not None:
                values.append({"date": s.started_at, "value": v, "session_id": s.id})
        if len(values) < 2:
            return None

        first_half = [v["value"] for v in values[:len(values)//2]]
        second_half = [v["value"] for v in values[len(values)//2:]]
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0

        direction = "stable"
        change_pct = 0
        if avg_first > 0:
            change_pct = ((avg_second - avg_first) / avg_first) * 100
            if change_pct > 5:
                direction = "improving"
            elif change_pct < -5:
                direction = "declining"

        return {
            "current": values[-1]["value"] if values else 0,
            "average": round(sum(v["value"] for v in values) / len(values), 4),
            "min": min(v["value"] for v in values),
            "max": max(v["value"] for v in values),
            "first_avg": round(avg_first, 4),
            "second_avg": round(avg_second, 4),
            "change_pct": round(change_pct, 1),
            "direction": direction,
            "data_points": len(values),
            "values": [{"date": v["date"].isoformat() if v["date"] else "", "value": v["value"]} for v in values],
        }

    def _get_metric_value(self, session: Session, metric: str) -> Optional[float]:
        mapping = {
            "overall_score": session.overall_score,
            "average_wpm": session.average_wpm,
            "filler_rate": session.filler_rate,
            "grammar_error_rate": min(1.0, (session.grammar_error_count or 0) / max(1, (session.word_count or 1)) * 10) if session.word_count else None,
            "average_eye_contact": session.average_eye_contact,
            "average_posture": session.average_posture,
            "confidence_score": session.confidence_score,
            "engagement_score": session.engagement_score,
            "clarity_score": session.clarity_score,
            "pace_consistency": session.pace_consistency,
        }
        return mapping.get(metric)

    def _summarize_directions(self, trends: Dict) -> Dict:
        improving = []
        declining = []
        stable = []
        for metric, data in trends.items():
            direction = data.get("direction", "stable")
            label = metric.replace("_", " ").title()
            if direction == "improving":
                improving.append({"metric": metric, "label": label, "change": data["change_pct"]})
            elif direction == "declining":
                declining.append({"metric": metric, "label": label, "change": data["change_pct"]})
            else:
                stable.append({"metric": metric, "label": label})
        return {"improving": improving, "declining": declining, "stable": stable}

    def _compute_weekly_averages(self, sessions: List[Session]) -> List[Dict]:
        weeks = defaultdict(list)
        for s in sessions:
            if s.started_at:
                week_start = s.started_at - datetime.timedelta(days=s.started_at.weekday())
                week_key = week_start.strftime("%Y-%m-%d")
                weeks[week_key].append(s)

        result = []
        for week_key in sorted(weeks.keys()):
            week_sessions = weeks[week_key]
            if not week_sessions:
                continue
            result.append({
                "week": week_key,
                "session_count": len(week_sessions),
                "avg_overall": round(sum(s.overall_score or 0 for s in week_sessions) / len(week_sessions), 2),
                "avg_confidence": round(sum(s.confidence_score or 0 for s in week_sessions) / len(week_sessions), 2),
                "avg_eye_contact": round(sum(s.average_eye_contact or 0 for s in week_sessions) / len(week_sessions), 2),
                "avg_posture": round(sum(s.average_posture or 0 for s in week_sessions) / len(week_sessions), 2),
                "avg_wpm": round(sum(s.average_wpm or 0 for s in week_sessions) / len(week_sessions), 1),
                "avg_filler_rate": round(sum(s.filler_rate or 0 for s in week_sessions) / len(week_sessions), 4),
                "total_practice_minutes": round(sum((s.duration_seconds or 0) for s in week_sessions) / 60, 0),
            })
        return result

    def get_metric_history(self, user_id: int, db: DbSession, metric: str, days: int = 30) -> List[Dict]:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.started_at >= cutoff,
            Session.ended_at.isnot(None),
        ).order_by(Session.started_at.asc()).all()

        results = []
        for s in sessions:
            v = self._get_metric_value(s, metric)
            if v is not None:
                results.append({
                    "date": s.started_at.isoformat() if s.started_at else "",
                    "value": v,
                    "session_id": s.id,
                })
        return results
