import datetime
from typing import Dict, List, Optional
from talkcraft_enterprise.utils.logger import get_logger

logger = get_logger("behavioral_intelligence")


COMMUNICATION_PATTERNS = {
    "rapid_fire": {"label": "Rapid Fire Speaker", "description": "Speaks quickly with short pauses", "indicator": "high_wpm_high_utterance"},
    "thoughtful_pauser": {"label": "Thoughtful Pauser", "description": "Takes frequent pauses to gather thoughts", "indicator": "low_wpm_high_pause"},
    "dominator": {"label": "Conversation Dominator", "description": "Tends to dominate speaking time", "indicator": "high_word_share"},
    "active_listener": {"label": "Active Listener", "description": "Engages through questions and acknowledgments", "indicator": "high_engagement_balanced"},
    "structured_speaker": {"label": "Structured Speaker", "description": "Organizes thoughts with clear structure", "indicator": "high_clarity_high_grammar"},
    "expressive_communicator": {"label": "Expressive Communicator", "description": "Uses varied tone and gestures", "indicator": "high_gesture_varied_pace"},
    "concise_speaker": {"label": "Concise Speaker", "description": "Gets to the point efficiently", "indicator": "low_word_count_high_clarity"},
}


class BehavioralIntelligence:
    def analyze_patterns(self, sessions_data: List[Dict]) -> Dict:
        if not sessions_data:
            return {"available": False}
        patterns = []
        for pattern_id, pattern in COMMUNICATION_PATTERNS.items():
            score = self._score_pattern(pattern_id, sessions_data)
            if score > 0.3:
                patterns.append({
                    "pattern_id": pattern_id,
                    "label": pattern["label"],
                    "description": pattern["description"],
                    "confidence": round(score, 2),
                })
        patterns.sort(key=lambda x: x["confidence"], reverse=True)
        dominant = patterns[0]["label"] if patterns else "Balanced Communicator"
        return {
            "available": True,
            "dominant_style": dominant,
            "patterns_detected": patterns,
            "sessions_analyzed": len(sessions_data),
        }

    def _score_pattern(self, pattern_id: str, sessions: List[Dict]) -> float:
        total = len(sessions)
        if total == 0:
            return 0.0
        matches = 0
        for s in sessions:
            if self._check_pattern(pattern_id, s):
                matches += 1
        return matches / total

    def _check_pattern(self, pattern_id: str, session: Dict) -> bool:
        wpm = session.get("avg_wpm", 0)
        clarity = session.get("scores", {}).get("clarity", 0) if isinstance(session.get("scores"), dict) else session.get("clarity_score", 0)
        engagement = session.get("scores", {}).get("engagement", 0) if isinstance(session.get("scores"), dict) else session.get("engagement_score", 0)
        word_count = session.get("word_count", 0)
        grammar = session.get("grammar_errors", 0)
        filler = session.get("filler_rate", 0)
        eye_contact = session.get("eye_contact", 0) if isinstance(session.get("eye_contact"), (int, float)) else session.get("average_eye_contact", 0)
        if pattern_id == "rapid_fire":
            return wpm > 170 and filler < 0.05
        if pattern_id == "thoughtful_pauser":
            return 80 < wpm < 130
        if pattern_id == "dominator":
            return word_count > 300
        if pattern_id == "active_listener":
            return engagement > 0.7 and word_count < 200
        if pattern_id == "structured_speaker":
            return clarity > 0.7 and grammar < 2
        if pattern_id == "expressive_communicator":
            return eye_contact > 0.7 and wpm > 150
        if pattern_id == "concise_speaker":
            return word_count < 100 and clarity > 0.8
        return False

    def analyze_sentiment_trend(self, sessions: List[Dict]) -> Dict:
        if not sessions:
            return {"available": False}
        sentiments = []
        for s in sessions:
            confidence = s.get("confidence_score", 0) if isinstance(s.get("confidence_score"), (int, float)) else s.get("scores", {}).get("confidence", 0)
            if isinstance(confidence, dict):
                confidence = 0
            sentiments.append({
                "date": s.get("date", ""),
                "confidence": confidence,
                "engagement": s.get("engagement_score", 0) if isinstance(s.get("engagement_score"), (int, float)) else s.get("scores", {}).get("engagement", 0),
            })
        avg_confidence = sum(s["confidence"] for s in sentiments) / len(sentiments) if sentiments else 0
        avg_engagement = sum(s["engagement"] for s in sentiments) / len(sentiments) if sentiments else 0
        trend = "improving" if len(sentiments) >= 2 and sentiments[-1]["confidence"] > sentiments[0]["confidence"] else "stable"
        return {
            "available": True,
            "average_confidence": round(avg_confidence, 2),
            "average_engagement": round(avg_engagement, 2),
            "trend": trend,
            "data_points": sentiments[-10:] if len(sentiments) > 10 else sentiments,
        }

    def generate_behavioral_report(self, user_id: int, db_session) -> Dict:
        from talkcraft_enterprise.database.models import BehavioralProfile
        profile = db_session.query(BehavioralProfile).filter(BehavioralProfile.user_id == user_id).first()
        if not profile:
            return {"available": False}
        return {
            "available": True,
            "communication_style": profile.communication_style,
            "dominant_patterns": profile.dominant_patterns,
            "emotional_tone": profile.emotional_tone,
            "speaking_traits": profile.speaking_traits,
            "last_analyzed": profile.last_analyzed.isoformat() if profile.last_analyzed else "",
        }


behavioral_intelligence = BehavioralIntelligence()
