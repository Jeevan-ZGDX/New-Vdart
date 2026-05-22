from dataclasses import dataclass, field
from typing import Dict, Optional
import time

from talkcraft_ai.utils.config import config
from talkcraft_ai.scoring.engagement import EngagementScorer, EngagementScores
from talkcraft_ai.scoring.clarity import ClarityScorer, ClarityScores
from talkcraft_ai.conversation.memory import ConversationMemory
from talkcraft_ai.utils.logger import get_logger

logger = get_logger("conversation_scorer")


@dataclass
class ConversationScores:
    grammar: float = 0.0
    filler: float = 0.0
    pace: float = 0.0
    eye_contact: float = 0.0
    posture: float = 0.0
    hand_gesture: float = 0.0
    engagement: float = 0.0
    clarity: float = 0.0
    confidence: float = 0.0
    overall: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConversationScoreHistory:
    scores: list = field(default_factory=list)
    best: float = 0.0
    worst: float = 1.0
    average: float = 0.0
    trend: str = "stable"
    total_turns: int = 0


class ConversationScorer:
    def __init__(self):
        self._weights = config.scoring
        self._engagement_scorer = EngagementScorer()
        self._clarity_scorer = ClarityScorer()
        self._history = ConversationScoreHistory()
        self._current_scores = ConversationScores()
        logger.info("ConversationScorer initialized")

    @property
    def current(self) -> ConversationScores:
        return self._current_scores

    @property
    def history(self) -> ConversationScoreHistory:
        return self._history

    def update_from_analysis(self, analysis: Dict) -> None:
        self._current_scores.grammar = analysis.get("grammar_score", self._current_scores.grammar)
        self._current_scores.filler = analysis.get("filler_score", self._current_scores.filler)
        self._current_scores.pace = analysis.get("pace_score", self._current_scores.pace)

    def update_from_vision(self, vision: Dict) -> None:
        self._current_scores.eye_contact = vision.get("eye_contact", self._current_scores.eye_contact)
        self._current_scores.posture = vision.get("posture", self._current_scores.posture)
        self._current_scores.hand_gesture = vision.get("hand_gesture", self._current_scores.hand_gesture)
        self._current_scores.confidence = vision.get("confidence", self._current_scores.confidence)

    def update_from_conversation(self, user_message: str, memory: ConversationMemory,
                                  filler_rate: float = 0.0) -> None:
        engagement = self._engagement_scorer.score(
            user_message,
            memory.get_history(include_metadata=True),
            memory.topic,
        )
        clarity = self._clarity_scorer.score(user_message, filler_rate)
        self._current_scores.engagement = engagement.overall
        self._current_scores.clarity = clarity.overall
        self._compute_overall()

    def _compute_overall(self) -> None:
        w = self._weights
        overall = (
            self._current_scores.grammar * w.grammar_weight
            + (1.0 - self._current_scores.filler) * w.filler_weight
            + self._current_scores.pace * w.pace_weight
            + self._current_scores.eye_contact * w.eye_contact_weight
            + self._current_scores.posture * w.posture_weight
            + self._current_scores.hand_gesture * w.hand_gesture_weight
            + self._current_scores.engagement * w.engagement_weight
            + self._current_scores.clarity * w.clarity_weight
            + self._current_scores.confidence * w.confidence_weight
        )
        self._current_scores.overall = min(1.0, overall)
        self._current_scores.timestamp = time.time()

    def record_turn(self) -> None:
        self._history.scores.append({
            "overall": self._current_scores.overall,
            "engagement": self._current_scores.engagement,
            "clarity": self._current_scores.clarity,
            "timestamp": self._current_scores.timestamp,
        })
        self._history.total_turns += 1
        scores_list = [s["overall"] for s in self._history.scores]
        if scores_list:
            self._history.best = max(scores_list)
            self._history.worst = min(scores_list)
            self._history.average = sum(scores_list) / len(scores_list)
            if len(scores_list) >= 3:
                recent = scores_list[-3:]
                if recent[-1] > recent[0] * 1.05:
                    self._history.trend = "improving"
                elif recent[-1] < recent[0] * 0.95:
                    self._history.trend = "declining"
                else:
                    self._history.trend = "stable"

    def get_scores_dict(self) -> Dict:
        return {
            "grammar": round(self._current_scores.grammar, 2),
            "filler": round(self._current_scores.filler, 2),
            "pace": round(self._current_scores.pace, 2),
            "eye_contact": round(self._current_scores.eye_contact, 2),
            "posture": round(self._current_scores.posture, 2),
            "hand_gesture": round(self._current_scores.hand_gesture, 2),
            "engagement": round(self._current_scores.engagement, 2),
            "clarity": round(self._current_scores.clarity, 2),
            "confidence": round(self._current_scores.confidence, 2),
            "overall": round(self._current_scores.overall, 2),
            "trend": self._history.trend,
            "average": round(self._history.average, 2),
            "total_turns": self._history.total_turns,
        }

    def reset(self) -> None:
        self._current_scores = ConversationScores()
        self._history = ConversationScoreHistory()
