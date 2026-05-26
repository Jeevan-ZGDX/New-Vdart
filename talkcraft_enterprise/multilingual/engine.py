import datetime
from typing import Dict, List, Optional
from talkcraft_enterprise.utils.logger import get_logger
from talkcraft_enterprise.multilingual.languages import language_manager, LANGUAGE_DEFINITIONS

logger = get_logger("multilingual_engine")


class MultilingualEngine:
    def __init__(self):
        self._active_sessions: Dict[int, Dict] = {}

    def start_session(self, user_id: int, language: str, session_type: str = "practice") -> Dict:
        lang_info = language_manager.get_language(language)
        if not lang_info:
            lang_info = language_manager.get_language("en")

        greeting = language_manager.get_phrase(language, "greeting")
        session = {
            "user_id": user_id,
            "language": language,
            "session_type": session_type,
            "started_at": datetime.datetime.utcnow().isoformat(),
            "metrics": {
                "pronunciation_score": 0.0,
                "fluency_score": 0.0,
                "grammar_score": 0.0,
                "overall_score": 0.0,
                "word_count": 0,
                "error_count": 0,
            },
            "feedback": [],
            "transcript": [],
        }
        self._active_sessions[user_id] = session
        return {
            "session_started": True,
            "language": lang_info["name"],
            "language_code": language,
            "greeting": greeting,
            "difficulty": lang_info.get("difficulty", "beginner"),
        }

    def process_transcription(self, user_id: int, text: str, metrics: Optional[Dict] = None) -> Dict:
        session = self._active_sessions.get(user_id)
        if not session:
            return {"error": "No active session"}

        session["transcript"].append({"text": text, "timestamp": datetime.datetime.utcnow().isoformat()})
        if metrics:
            for key, value in metrics.items():
                if key in session["metrics"]:
                    session["metrics"][key] = value

        lang = session["language"]
        feedback = self._generate_feedback(text, lang, session["metrics"])
        if feedback:
            session["feedback"].append(feedback)

        return {
            "processed": True,
            "language": lang,
            "metrics": session["metrics"],
            "feedback": feedback,
            "word_count": len(text.split()),
        }

    def end_session(self, user_id: int) -> Dict:
        session = self._active_sessions.pop(user_id, None)
        if not session:
            return {"error": "No active session"}
        duration = (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(session["started_at"])).seconds
        session["duration_seconds"] = duration
        session["ended_at"] = datetime.datetime.utcnow().isoformat()
        return {
            "session_ended": True,
            "language": session["language"],
            "duration_seconds": duration,
            "final_metrics": session["metrics"],
            "total_feedback": len(session["feedback"]),
            "transcript_length": len(session["transcript"]),
        }

    def get_session_state(self, user_id: int) -> Optional[Dict]:
        return self._active_sessions.get(user_id)

    def _generate_feedback(self, text: str, lang: str, metrics: Dict) -> Optional[Dict]:
        issues = []
        words = text.split()
        word_count = len(words)

        if word_count < 3:
            return None

        if metrics.get("fluency_score", 1.0) < 0.5:
            issues.append(language_manager.get_phrase(lang, "feedback_constructive"))

        if metrics.get("pronunciation_score", 1.0) < 0.6:
            issues.append(f"Focus on pronunciation in {LANGUAGE_DEFINITIONS.get(lang, {}).get('name', lang)}")

        if metrics.get("grammar_score", 1.0) < 0.6:
            issues.append("Pay attention to grammar structure")

        if not issues:
            if metrics.get("overall_score", 0) > 0.7:
                return {"type": "positive", "message": language_manager.get_phrase(lang, "feedback_positive"), "metrics": metrics}
            return {"type": "encouragement", "message": language_manager.get_phrase(lang, "encouragement"), "metrics": metrics}

        return {"type": "constructive", "message": " ".join(issues[:2]), "metrics": metrics}

    def analyze_pronunciation(self, text: str, language: str, expected_text: str) -> Dict:
        text_words = set(text.lower().split())
        expected_words = set(expected_text.lower().split())
        if not expected_words:
            return {"accuracy": 1.0, "errors": []}
        correct = text_words & expected_words
        accuracy = len(correct) / len(expected_words) if expected_words else 1.0
        missing = expected_words - text_words
        extra = text_words - expected_words
        return {
            "accuracy": round(accuracy, 2),
            "correct_words": len(correct),
            "total_expected": len(expected_words),
            "missing_words": list(missing)[:5],
            "extra_words": list(extra)[:5],
        }


multilingual_engine = MultilingualEngine()
