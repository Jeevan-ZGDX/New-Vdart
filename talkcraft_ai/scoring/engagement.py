import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from talkcraft_ai.utils.logger import get_logger

logger = get_logger("engagement_scorer")


@dataclass
class EngagementScores:
    overall: float = 0.0
    response_length_score: float = 0.0
    question_asking: float = 0.0
    topic_relevance: float = 0.0
    expressiveness: float = 0.0
    conversation_balance: float = 0.0


class EngagementScorer:
    def __init__(self):
        self._question_words = {"what", "why", "how", "when", "where", "who", "which", "could", "would", "can", "do", "did", "is", "are", "was", "were", "have", "has", "had"}
        self._expressive_words = {"think", "believe", "feel", "wonder", "amazing", "interesting", "fascinating", "great", "wonderful", "exciting", "love", "enjoy", "passionate"}

    def score(self, user_message: str, history: List[Dict], topic: str = "") -> EngagementScores:
        scores = EngagementScores()
        if not user_message or not user_message.strip():
            return scores
        scores.response_length_score = self._score_response_length(user_message)
        scores.question_asking = self._score_question_asking(user_message)
        scores.topic_relevance = self._score_topic_relevance(user_message, topic)
        scores.expressiveness = self._score_expressiveness(user_message)
        scores.conversation_balance = self._score_conversation_balance(user_message, history)
        weights = {
            "response_length_score": 0.20,
            "question_asking": 0.25,
            "topic_relevance": 0.20,
            "expressiveness": 0.15,
            "conversation_balance": 0.20,
        }
        scores.overall = (
            scores.response_length_score * weights["response_length_score"]
            + scores.question_asking * weights["question_asking"]
            + scores.topic_relevance * weights["topic_relevance"]
            + scores.expressiveness * weights["expressiveness"]
            + scores.conversation_balance * weights["conversation_balance"]
        )
        return scores

    def _score_response_length(self, text: str) -> float:
        words = len(text.split())
        if words < 3:
            return 0.2
        elif words < 8:
            return 0.5
        elif words < 15:
            return 0.7
        elif words < 50:
            return 0.9
        elif words < 100:
            return 1.0
        else:
            return 0.8

    def _score_question_asking(self, text: str) -> float:
        sentences = re.split(r'[.!?]+', text)
        question_sentences = [s for s in sentences if s.strip().endswith("?")]
        if not question_sentences:
            words = text.lower().split()
            question_word_count = sum(1 for w in words if w in self._question_words)
            return min(0.3, question_word_count * 0.1)
        ratio = len(question_sentences) / max(len([s for s in sentences if s.strip()]), 1)
        return min(1.0, ratio * 3.0)

    def _score_topic_relevance(self, text: str, topic: str) -> float:
        if not topic:
            return 0.7
        topic_words = set(topic.lower().split())
        text_words = set(text.lower().split())
        if not topic_words:
            return 0.7
        overlap = len(topic_words & text_words)
        return min(1.0, overlap / max(len(topic_words), 1) * 2.0)

    def _score_expressiveness(self, text: str) -> float:
        words = text.lower().split()
        expressive_count = sum(1 for w in words if w in self._expressive_words)
        base = min(1.0, expressive_count * 0.2)
        exclamation = text.count("!")
        if exclamation > 0:
            base = min(1.0, base + 0.1)
        has_personal_pronouns = any(p in words for p in ["i", "me", "my", "we", "our"])
        if has_personal_pronouns:
            base = min(1.0, base + 0.15)
        return base

    def _score_conversation_balance(self, user_message: str, history: List[Dict]) -> float:
        if not history:
            return 0.7
        user_turns = sum(1 for h in history if h.get("role") == "user")
        ai_turns = sum(1 for h in history if h.get("role") == "assistant")
        total = user_turns + ai_turns
        if total == 0:
            return 0.7
        user_ratio = user_turns / total
        if 0.3 <= user_ratio <= 0.7:
            return 1.0
        elif 0.2 <= user_ratio <= 0.8:
            return 0.7
        else:
            return 0.4
