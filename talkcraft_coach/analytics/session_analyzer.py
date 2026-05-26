import datetime
from typing import Dict, List, Optional
from talkcraft_coach.database.models import Session
from talkcraft_coach.utils.logger import get_logger

logger = get_logger("session_analyzer")


class SessionAnalyzer:
    def analyze_session(self, session: Session) -> Dict:
        scores = {
            "overall": session.overall_score or 0,
            "speech_quality": self._compute_speech_quality(session),
            "presence": self._compute_presence(session),
            "engagement": session.engagement_score or 0,
            "clarity": session.clarity_score or 0,
        }
        weaknesses = self._detect_weaknesses(session)
        strengths = self._detect_strengths(session)
        duration_min = max(1, (session.duration_seconds or 0) / 60)
        return {
            "session_id": session.id,
            "date": session.started_at.isoformat() if session.started_at else "",
            "duration_minutes": round(duration_min, 1),
            "scores": scores,
            "weaknesses": weaknesses,
            "strengths": strengths,
            "word_count": session.word_count or 0,
            "filler_rate": round((session.filler_rate or 0) * 100, 1),
            "avg_wpm": round(session.average_wpm or 0, 1),
            "pace_consistency": round((session.pace_consistency or 0) * 100, 1),
            "grammar_errors": session.grammar_error_count or 0,
            "eye_contact": round((session.average_eye_contact or 0) * 100, 1),
            "posture": round((session.average_posture or 0) * 100, 1),
            "confidence": round((session.confidence_score or 0) * 100, 1),
            "mode": session.mode or "",
            "topic": session.topic or "",
            "difficulty": session.difficulty or "",
            "summary": session.ai_summary or "",
        }

    def _compute_speech_quality(self, session: Session) -> float:
        wpm_score = self._wpm_score(session.average_wpm or 0)
        filler_penalty = max(0, 1.0 - (session.filler_rate or 0) * 3)
        grammar_penalty = max(0, 1.0 - min(1.0, (session.grammar_error_count or 0) / max(1, (session.word_count or 1)) * 20))
        pace_consistency = session.pace_consistency or 0.5
        return round((wpm_score * 0.25 + filler_penalty * 0.25 + grammar_penalty * 0.25 + pace_consistency * 0.25), 2)

    def _compute_presence(self, session: Session) -> float:
        eye = session.average_eye_contact or 0
        posture = session.average_posture or 0
        confidence = session.confidence_score or 0
        return round((eye * 0.35 + posture * 0.35 + confidence * 0.30), 2)

    def _wpm_score(self, wpm: float) -> float:
        if 140 <= wpm <= 170:
            return 1.0
        if 120 <= wpm <= 190:
            return 0.8
        if 100 <= wpm <= 210:
            return 0.6
        if wpm > 0:
            return 0.4
        return 0.0

    def _detect_weaknesses(self, session: Session) -> List[Dict]:
        weaknesses = []
        threshold = 0.6
        if (session.filler_rate or 0) > 0.05:
            weaknesses.append({
                "area": "filler_words",
                "label": "Filler Words",
                "score": max(0, 1.0 - (session.filler_rate or 0) * 5),
                "severity": "high" if (session.filler_rate or 0) > 0.1 else "medium",
            })
        if (session.average_wpm or 0) < 100:
            weaknesses.append({
                "area": "speaking_pace",
                "label": "Speaking Pace (Too Slow)",
                "score": self._wpm_score(session.average_wpm or 0),
                "severity": "medium",
            })
        elif (session.average_wpm or 0) > 210:
            weaknesses.append({
                "area": "speaking_pace",
                "label": "Speaking Pace (Too Fast)",
                "score": self._wpm_score(session.average_wpm or 0),
                "severity": "high",
            })
        if (session.average_eye_contact or 0) < threshold:
            weaknesses.append({
                "area": "eye_contact",
                "label": "Eye Contact",
                "score": session.average_eye_contact or 0,
                "severity": "high" if (session.average_eye_contact or 0) < 0.4 else "medium",
            })
        if (session.average_posture or 0) < threshold:
            weaknesses.append({
                "area": "posture",
                "label": "Posture Stability",
                "score": session.average_posture or 0,
                "severity": "high" if (session.average_posture or 0) < 0.4 else "medium",
            })
        if (session.confidence_score or 0) < threshold:
            weaknesses.append({
                "area": "confidence",
                "label": "Confidence",
                "score": session.confidence_score or 0,
                "severity": "high" if (session.confidence_score or 0) < 0.3 else "medium",
            })
        if (session.grammar_error_count or 0) > 0 and (session.word_count or 0) > 0:
            error_rate = session.grammar_error_count / max(1, session.word_count)
            if error_rate > 0.05:
                weaknesses.append({
                    "area": "grammar",
                    "label": "Grammar",
                    "score": max(0, 1.0 - error_rate * 5),
                    "severity": "high" if error_rate > 0.1 else "medium",
                })
        if (session.engagement_score or 0) < threshold:
            weaknesses.append({
                "area": "engagement",
                "label": "Engagement",
                "score": session.engagement_score or 0,
                "severity": "medium",
            })
        if (session.clarity_score or 0) < threshold:
            weaknesses.append({
                "area": "clarity",
                "label": "Clarity",
                "score": session.clarity_score or 0,
                "severity": "medium",
            })
        return weaknesses

    def _detect_strengths(self, session: Session) -> List[Dict]:
        strengths = []
        threshold = 0.8
        if (session.average_eye_contact or 0) > threshold:
            strengths.append({"area": "eye_contact", "label": "Strong Eye Contact", "score": session.average_eye_contact})
        if (session.average_posture or 0) > threshold:
            strengths.append({"area": "posture", "label": "Excellent Posture", "score": session.average_posture})
        if (session.confidence_score or 0) > threshold:
            strengths.append({"area": "confidence", "label": "High Confidence", "score": session.confidence_score})
        if (session.engagement_score or 0) > threshold:
            strengths.append({"area": "engagement", "label": "High Engagement", "score": session.engagement_score})
        if (session.clarity_score or 0) > threshold:
            strengths.append({"area": "clarity", "label": "Excellent Clarity", "score": session.clarity_score})
        if (session.filler_rate or 0) < 0.02:
            strengths.append({"area": "filler_words", "label": "Minimal Filler Words", "score": 1.0 - (session.filler_rate or 0)})
        return strengths
