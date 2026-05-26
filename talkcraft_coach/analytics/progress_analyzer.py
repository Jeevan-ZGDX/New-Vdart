import datetime
from collections import defaultdict
from typing import Dict, List, Optional
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.models import Session, Progress, User
from talkcraft_coach.utils.logger import get_logger
from talkcraft_coach.utils.config import config

logger = get_logger("progress_analyzer")


class ProgressAnalyzer:
    def get_user_summary(self, user_id: int, db: DbSession) -> Dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"available": False}

        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.ended_at.isnot(None),
        ).order_by(Session.started_at.desc()).all()

        if not sessions:
            return {"available": False, "user": self._user_info(user)}

        total_sessions = len(sessions)
        total_duration = sum(s.duration_seconds or 0 for s in sessions) / 60
        avg_score = sum(s.overall_score or 0 for s in sessions) / total_sessions if total_sessions else 0
        latest = sessions[0]
        recent_5 = sessions[:5]
        recent_avg = sum(s.overall_score or 0 for s in recent_5) / len(recent_5) if recent_5 else 0

        first_5 = sessions[-5:] if len(sessions) >= 5 else sessions
        first_avg = sum(s.overall_score or 0 for s in first_5) / len(first_5) if first_5 else 0
        improvement = recent_avg - first_avg

        return {
            "available": True,
            "user": self._user_info(user),
            "total_sessions": total_sessions,
            "total_practice_minutes": round(total_duration, 1),
            "average_score": round(avg_score, 2),
            "latest_score": round(latest.overall_score or 0, 2),
            "recent_average": round(recent_avg, 2),
            "improvement": round(improvement, 2),
            "improvement_pct": round((improvement / max(0.01, first_avg)) * 100, 1) if first_avg > 0 else 0,
            "current_streak": self._compute_streak(sessions),
            "last_session_date": latest.started_at.isoformat() if latest.started_at else "",
            "last_session_mode": latest.mode or "",
            "last_session_score": round(latest.overall_score or 0, 2),
        }

    def get_weekly_summary(self, user_id: int, db: DbSession) -> Dict:
        week_start = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        week_sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.started_at >= week_start,
            Session.ended_at.isnot(None),
        ).all()

        if not week_sessions:
            return {"available": False, "message": "No sessions this week"}

        scores = {
            "overall": [s.overall_score or 0 for s in week_sessions],
            "confidence": [s.confidence_score or 0 for s in week_sessions],
            "eye_contact": [s.average_eye_contact or 0 for s in week_sessions],
            "posture": [s.average_posture or 0 for s in week_sessions],
            "wpm": [s.average_wpm or 0 for s in week_sessions],
            "filler_rate": [s.filler_rate or 0 for s in week_sessions],
        }

        total_duration = sum(s.duration_seconds or 0 for s in week_sessions) / 60
        prev_week_start = week_start - datetime.timedelta(days=7)
        prev_sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.started_at >= prev_week_start,
            Session.started_at < week_start,
            Session.ended_at.isnot(None),
        ).all()
        prev_avg = sum(s.overall_score or 0 for s in prev_sessions) / max(1, len(prev_sessions))

        return {
            "available": True,
            "session_count": len(week_sessions),
            "total_practice_minutes": round(total_duration, 1),
            "average_scores": {k: round(sum(v) / len(v), 2) for k, v in scores.items()},
            "best_score": round(max(s.overall_score or 0 for s in week_sessions), 2),
            "improvement_vs_prev_week": round(
                (sum(s.overall_score or 0 for s in week_sessions) / len(week_sessions)) - prev_avg, 2
            ),
            "sessions": [
                {
                    "id": s.id,
                    "date": s.started_at.isoformat() if s.started_at else "",
                    "mode": s.mode or "",
                    "score": round(s.overall_score or 0, 2),
                    "duration": round((s.duration_seconds or 0) / 60, 1),
                }
                for s in week_sessions
            ],
        }

    def compute_weekly_progress(self, user_id: int, db: DbSession) -> List[Dict]:
        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.ended_at.isnot(None),
        ).order_by(Session.started_at.asc()).all()

        weeks = defaultdict(list)
        for s in sessions:
            if s.started_at:
                ws = s.started_at - datetime.timedelta(days=s.started_at.weekday())
                weeks[ws.strftime("%Y-%m-%d")].append(s)

        result = []
        for wk in sorted(weeks.keys()):
            ws = weeks[wk]
            result.append({
                "week": wk,
                "sessions": len(ws),
                "avg_score": round(sum(s.overall_score or 0 for s in ws) / len(ws), 2),
                "avg_confidence": round(sum(s.confidence_score or 0 for s in ws) / len(ws), 2),
                "avg_wpm": round(sum(s.average_wpm or 0 for s in ws) / len(ws), 1),
                "avg_filler": round(sum(s.filler_rate or 0 for s in ws) / len(ws), 4),
                "total_minutes": round(sum(s.duration_seconds or 0 for s in ws) / 60, 1),
            })
        return result

    def _user_info(self, user: User) -> Dict:
        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name or user.username,
            "skill_level": user.skill_level or "beginner",
            "total_sessions": user.total_sessions or 0,
            "total_practice_time_minutes": user.total_practice_time_minutes or 0,
            "created_at": user.created_at.isoformat() if user.created_at else "",
        }

    def _compute_streak(self, sessions: List[Session]) -> Dict:
        if not sessions:
            return {"current": 0, "longest": 0}
        dates = sorted(set(
            s.started_at.date() for s in sessions if s.started_at
        ), reverse=True)
        if not dates:
            return {"current": 0, "longest": 0}

        longest = 1
        current = 0
        streak = 1
        for i in range(len(dates) - 1):
            diff = (dates[i] - dates[i + 1]).days
            if diff == 1:
                streak += 1
                longest = max(longest, streak)
            else:
                streak = 1

        today = datetime.datetime.utcnow().date()
        yesterday = today - datetime.timedelta(days=1)
        if dates[0] == today or dates[0] == yesterday:
            current = 1
            for i in range(len(dates) - 1):
                if (dates[i] - dates[i + 1]).days == 1:
                    current += 1
                else:
                    break

        return {"current": current, "longest": longest or 1}

    def get_grammar_improvement(self, user_id: int, db: DbSession) -> Dict:
        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.ended_at.isnot(None),
            Session.word_count > 0,
        ).order_by(Session.started_at.asc()).all()

        if len(sessions) < 2:
            return {"available": False}

        rates = []
        for i, s in enumerate(sessions):
            error_rate = (s.grammar_error_count or 0) / max(1, (s.word_count or 1))
            rates.append({
                "session_index": i,
                "date": s.started_at.isoformat() if s.started_at else "",
                "error_rate": round(error_rate, 4),
                "error_count": s.grammar_error_count or 0,
                "word_count": s.word_count or 0,
            })

        first_half = sum(r["error_rate"] for r in rates[:len(rates)//2]) / max(1, len(rates)//2)
        second_half = sum(r["error_rate"] for r in rates[len(rates)//2:]) / max(1, len(rates) - len(rates)//2)
        improvement = first_half - second_half

        return {
            "available": True,
            "current_rate": rates[-1]["error_rate"],
            "initial_rate": rates[0]["error_rate"],
            "average_rate": round(sum(r["error_rate"] for r in rates) / len(rates), 4),
            "improvement": round(improvement, 4),
            "improvement_pct": round((improvement / max(0.0001, first_half)) * 100, 1) if first_half > 0 else 0,
            "data_points": rates,
            "trend": "improving" if improvement > 0.01 else ("declining" if improvement < -0.01 else "stable"),
        }
