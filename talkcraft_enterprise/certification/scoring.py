import datetime
import uuid
from typing import Dict, List, Optional
from talkcraft_enterprise.utils.logger import get_logger
from talkcraft_enterprise.utils.config import config

logger = get_logger("certification")


CERTIFICATION_LEVELS = {
    "bronze": {
        "name": "Bronze Communicator",
        "min_score": 0.6,
        "description": "Foundational communication skills",
        "requirements": ["Complete 5 sessions", "Average score > 60%", "No critical weaknesses"],
    },
    "silver": {
        "name": "Silver Communicator",
        "min_score": 0.7,
        "description": "Developing communication competence",
        "requirements": ["Complete 15 sessions", "Average score > 70%", "Filler rate < 5%"],
    },
    "gold": {
        "name": "Gold Communicator",
        "min_score": 0.8,
        "description": "Advanced communication mastery",
        "requirements": ["Complete 30 sessions", "Average score > 80%", "Filler rate < 3%", "Grammar accuracy > 95%"],
    },
    "platinum": {
        "name": "Platinum Communicator",
        "min_score": 0.9,
        "description": "Exceptional communication excellence",
        "requirements": ["Complete 50 sessions", "Average score > 90%", "Filler rate < 2%", "Grammar accuracy > 98%", "All-rounder scores"],
    },
}


class CertificationScorer:
    def assess_level(self, user_stats: Dict) -> Dict:
        avg_score = user_stats.get("average_score", 0)
        total_sessions = user_stats.get("total_sessions", 0)
        filler_rate = user_stats.get("filler_rate", 1)
        grammar_accuracy = user_stats.get("grammar_accuracy", 1)

        achieved_levels = []
        next_level = None
        for level_id, level_info in CERTIFICATION_LEVELS.items():
            meets_reqs = self._check_requirements(level_info, avg_score, total_sessions, filler_rate, grammar_accuracy)
            if meets_reqs:
                achieved_levels.append({"id": level_id, "name": level_info["name"], "score": level_info["min_score"]})
            elif next_level is None:
                next_level = {"id": level_id, "name": level_info["name"], "min_score": level_info["min_score"], "gap": round(level_info["min_score"] - avg_score, 2)}

        current_level = achieved_levels[-1] if achieved_levels else {"id": "none", "name": "Not yet certified", "score": 0}
        return {
            "current_level": current_level,
            "achieved_levels": achieved_levels,
            "next_level": next_level,
            "progress_to_next": round((avg_score / (next_level["min_score"] if next_level else 1)) * 100, 1) if next_level else 100,
        }

    def _check_requirements(self, level: Dict, avg_score: float, sessions: int, filler_rate: float, grammar_acc: float) -> bool:
        if avg_score < level["min_score"]:
            return False
        reqs = " ".join(level.get("requirements", []))
        if "5 sessions" in reqs and sessions < 5:
            return False
        if "15 sessions" in reqs and sessions < 15:
            return False
        if "30 sessions" in reqs and sessions < 30:
            return False
        if "50 sessions" in reqs and sessions < 50:
            return False
        if "Filler rate < 5%" in reqs and filler_rate > 0.05:
            return False
        if "Filler rate < 3%" in reqs and filler_rate > 0.03:
            return False
        if "Filler rate < 2%" in reqs and filler_rate > 0.02:
            return False
        if "Grammar accuracy > 95%" in reqs and grammar_acc < 0.95:
            return False
        if "Grammar accuracy > 98%" in reqs and grammar_acc < 0.98:
            return False
        return True

    def evaluate_session_for_certification(self, session_data: Dict) -> Dict:
        scores = session_data.get("scores", {})
        overall = scores.get("overall", session_data.get("overall_score", 0))
        filler = session_data.get("filler_rate", 0)
        grammar = session_data.get("grammar_errors", 0)
        word_count = session_data.get("word_count", 1)
        grammar_rate = max(0, 1.0 - (grammar / max(1, word_count)) * 10)
        eye = session_data.get("eye_contact", 0) if isinstance(session_data.get("eye_contact"), (int, float)) else session_data.get("average_eye_contact", 0)
        posture = session_data.get("posture", 0) if isinstance(session_data.get("posture"), (int, float)) else session_data.get("average_posture", 0)
        confidence = session_data.get("confidence", 0) if isinstance(session_data.get("confidence"), (int, float)) else session_data.get("confidence_score", 0)
        if isinstance(overall, dict):
            overall = 0
        if isinstance(eye, dict):
            eye = 0
        if isinstance(posture, dict):
            posture = 0
        if isinstance(confidence, dict):
            confidence = 0
        return {
            "overall_score": round(overall, 2),
            "filler_rate": round(filler, 4),
            "grammar_accuracy": round(grammar_rate, 2),
            "eye_contact": round(eye, 2),
            "posture": round(posture, 2),
            "confidence": round(confidence, 2),
            "composite": round((overall * 0.3 + grammar_rate * 0.2 + eye * 0.2 + posture * 0.15 + confidence * 0.15), 2),
        }

    def generate_certificate(self, user_id: int, level: str, score: float, language: str = "en") -> Dict:
        cert_id = f"CERT-{level.upper()}-{uuid.uuid4().hex[:8].upper()}"
        level_info = CERTIFICATION_LEVELS.get(level, CERTIFICATION_LEVELS["bronze"])
        return {
            "certificate_id": cert_id,
            "user_id": user_id,
            "level": level,
            "level_name": level_info["name"],
            "score": round(score, 2),
            "language": language,
            "issued_at": datetime.datetime.utcnow().isoformat(),
            "valid_until": (datetime.datetime.utcnow() + datetime.timedelta(days=365)).isoformat(),
        }


certification_scorer = CertificationScorer()
